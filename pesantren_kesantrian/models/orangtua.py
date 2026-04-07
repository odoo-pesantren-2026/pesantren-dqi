from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class OrangTua(models.Model):
    _inherit = 'cdn.orangtua'

    password = fields.Char(store=True)

    @api.model
    def create(self, vals):
        # Membuat record 'OrangTua' menggunakan inheritance
        res = super(OrangTua, self).create(vals)

        #  VALIDASI DUPLIKAT EMAIL DI res.users
        if res.email:
            existing_user = self.env['res.users'].sudo().search(
                [('login', '=', res.email)], limit=1)
            if existing_user:
                # Jika user sudah ada, gunakan user tersebut (sharing)
                res.user_id = existing_user.id
                if res.partner_id:
                    res.partner_id.user_id = existing_user.id

                # Pastikan user memiliki group yang diperlukan dan tidak konflik tipe user
                group_portal = self.env.ref(
                    'base.group_portal', raise_if_not_found=False)
                group_public = self.env.ref(
                    'base.group_public', raise_if_not_found=False)

                group_ids = [
                    self.env.ref('base.group_user').id,
                    self.env.ref(
                        'pesantren_kesantrian.group_kesantrian_orang_tua').id,
                    self.env.ref('pesantren_base.group_sekolah_user').id,
                    self.env.ref(
                        'pesantren_kesantrian.group_kesantrian_user').id,
                    self.env.ref('pesantren_guru.group_guru_user').id,
                    self.env.ref('pesantren_keuangan.group_keuangan_user').id,
                    self.env.ref('account.group_account_readonly').id,
                ]

                commands = []
                if group_portal:
                    commands.append((3, group_portal.id))  # Remove Portal
                if group_public:
                    commands.append((3, group_public.id))  # Remove Public
                commands += [(4, gid)
                             for gid in group_ids]  # Add required groups

                existing_user.sudo().write({
                    'groups_id': commands
                })
                return res

        # VALIDASI & SET DEFAULT PASSWORD (FIX ERROR BOOLEAN)
        if not res.password or not isinstance(res.password, str):
            # Set default password (bisa dari email atau fixed)
            # Ambil 8 char pertama email, atau default
            res.password = res.email[:8] if res.email else 'default123'

        # Membuat user baru dengan login berbasis email dan password default
        user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
            'login': res.email,  # Menggunakan email dari field model
            'name': res.name,  # Nama pengguna
            # Mengatur perusahaan default
            'company_id': self.env.ref('base.main_company').id,
            'partner_id': res.partner_id.id,  # Hubungkan dengan partner terkait
            # Password default (sekarang pasti string)
            'password': res.password,
            'groups_id': [(6, 0, [
                # Assign grup internal user (standard)
                self.env.ref('base.group_user').id,
                # Assign grup orang tua
                self.env.ref(
                    'pesantren_kesantrian.group_kesantrian_orang_tua').id,
                # Assign grup sekolah user
                self.env.ref('pesantren_base.group_sekolah_user').id,
                # Assign grup sekolah user
                self.env.ref('pesantren_kesantrian.group_kesantrian_user').id,
                # Assign grup guru user
                self.env.ref('pesantren_guru.group_guru_user').id,
                # Assign grup keuangan user
                self.env.ref('pesantren_keuangan.group_keuangan_user').id,
                self.env.ref('account.group_account_readonly').id,
            ])]
        })

        res.user_id = user.id

        if res.partner_id:
            res.partner_id.user_id = user.id

        return res

    def unlink(self):
        for orangtua in self:
            users = self.env['res.users'].search(
                [('partner_id', '=', orangtua.partner_id.id)])
            if users:
                partner = users.partner_id
                users.unlink()
                partner.unlink()
        return super(OrangTua, self).unlink()

    def update_user_groups(self):
        """Update groups for the related user using batch operations."""
        group_ids = [
            self.env.ref('base.group_user', raise_if_not_found=False),
            self.env.ref(
                'pesantren_kesantrian.group_kesantrian_orang_tua', raise_if_not_found=False),
            self.env.ref('pesantren_base.group_sekolah_user',
                         raise_if_not_found=False),
            self.env.ref('pesantren_kesantrian.group_kesantrian_user',
                         raise_if_not_found=False),
            self.env.ref('pesantren_guru.group_guru_user',
                         raise_if_not_found=False),
            self.env.ref('pesantren_keuangan.group_keuangan_user',
                         raise_if_not_found=False),
            self.env.ref('account.group_account_readonly',
                         raise_if_not_found=False),
        ]
        group_ids = [g.id for g in group_ids if g]

        # Batch find users
        users = self.mapped('user_id')

        # Check by email for records without user_id
        recs_without_user = self.filtered(lambda r: not r.user_id and r.email)
        if recs_without_user:
            emails = recs_without_user.mapped('email')
            found_users = self.env['res.users'].sudo().search(
                [('login', 'in', emails)])
            users |= found_users

        if users:
            users.sudo().write({
                'groups_id': [(4, gid) for gid in group_ids]
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Berhasil',
                'message': f'Hak Akses untuk {len(users)} user sudah diperbarui.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_user_id(self):
        """Synchronize user_id from cdn.orangtua to partner_id.user_id using high-performance SQL."""
        query = """
            UPDATE res_partner p
            SET user_id = o.user_id
            FROM cdn_orangtua o
            WHERE p.id = o.partner_id 
            AND o.user_id IS NOT NULL
            AND (p.user_id IS DISTINCT FROM o.user_id)
        """
        self._cr.execute(query)
        count = self._cr.rowcount

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Sinkronisasi Berhasil',
                'message': f'Berhasil menyelaraskan {count} data user secara instan.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        # Simpan dulu nilai password sebelum super().write()
        password_changed = 'password' in vals
        new_password = vals.get('password') if password_changed else None

        # Panggil super write terlebih dahulu
        res = super(OrangTua, self).write(vals)

        # Setelah record ter-update, baru update password user
        if password_changed and new_password:
            for record in self:
                if record.user_id:
                    # Update password user menggunakan sudo
                    record.user_id.sudo().write({'password': new_password})

        if 'user_id' in vals:
            for record in self:
                if record.partner_id:
                    record.partner_id.sudo().write(
                        {'user_id': record.user_id.id})

        return res
