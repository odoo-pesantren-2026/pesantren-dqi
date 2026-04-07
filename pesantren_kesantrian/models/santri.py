from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError

class Santri(models.Model):
    _inherit = 'cdn.siswa'
    _sql_constraints = [
        ('nis_unique', 'unique(nis)', 'NIS harus unik!'),
    ]
    partner_id          = fields.Many2one('res.partner', string='Siswa', required=True)
    last_tahfidz        = fields.Many2one('cdn.tahfidz_quran', string='Tahfidz Terakhir', readonly=True )
    tahfidz_terakhir_id = fields.Many2one(
        'cdn.penilaian_quran',
        string='Tahfidz Terakhir',
        compute='_compute_tahfidz_terakhir',
        store=False,
        readonly=True,
        ondelete='set null'
    )
    def action_view_tahfidz_terakhir(self):
        self.ensure_one()
        if not self.tahfidz_terakhir_id:
            raise UserError("Belum ada data tahfidz terakhir untuk santri ini.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.penilaian_quran',
            'view_mode': 'form',
            'res_id': self.tahfidz_terakhir_id.id,
            'target': 'current',
        }    
    ruang_kelas_id      = fields.Many2one('cdn.ruang_kelas', string='Ruang Kelas')
    kamar_id            = fields.Many2one('cdn.kamar_santri', string='Kamar', readonly=True)
    musyrif_id          = fields.Many2one('hr.employee', related='kamar_id.musyrif_id', string='Musyrif/Pembina', readonly=True)
    musyrif_ganti_ids   = fields.Many2many(comodel_name='hr.employee', related='kamar_id.pengganti_ids', string='Musyrif Pengganti', readonly=True)
    halaqoh_id          = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True)
    halaqoh_ids = fields.Many2many(
        'cdn.halaqoh',
        'cdn_siswa_halaqoh_rel',   # tabel relasi Many2many
        'siswa_id', 'halaqoh_m2m_id',
        string='Semua Halaqoh',
        readonly=True
    )
    penanggung_jawab_id = fields.Many2one(comodel_name='hr.employee', related='halaqoh_id.penanggung_jawab_id', string='Penanggung Jawab', readonly=True)
    pengganti_ids       = fields.Many2many(comodel_name ='hr.employee', related='halaqoh_id.pengganti_ids', string='Ustadz Pengganti', readonly=True)
    penanggung_jawab_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Semua Penanggung Jawab',
        compute='_compute_penanggung_jawab_ids',
        store=False
    )

    pengganti_all_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Semua Ustadz Pengganti',
        compute='_compute_pengganti_all_ids',
        store=False
    )
    tahfidz_quran_ids   = fields.One2many('cdn.penilaian_quran', 'siswa_id', string='Tahfidz Quran', readonly=True)

    #state info smart button
    kesehatan_count     = fields.Integer(string='Kesehatan', compute='_compute_count_kesehatan')
    pelanggaran_count   = fields.Integer(string='Pelanggaran', compute='_compute_count_pelanggaran')
    prestasi_siswa_count = fields.Integer(string='Prestasi', compute='_compute_count_prestasi')
    # tahfidz_quran_count = fields.Integer(string='Tahfidz Quran', compute='_compute_count_tahfidz_quran')
    
    penilaian_quran_count = fields.Integer(string='Penilaian Quran', compute='_compute_count_penilaian_quran')
    saldo_tagihan_count = fields.Float(string='Saldo Tagihan', compute='_compute_count_saldo_tagihan', widget="integer")
    uang_saku_count = fields.Float(string='Uang Saku', compute='_compute_count_uang_saku', widget="integer")
    
    saldo_tagihan_formatted = fields.Integer(string='Saldo Tagihan (Format)', compute='_compute_saldo_tagihan_formatted')
    uang_saku_formatted = fields.Integer(string='Uang Saku (Format)', compute='_compute_uang_saku_formatted')
    catatan_akun        = fields.Text(string="Catatan")
    alasan_akun         = fields.Char(string="Alasan")
    riwayat_hafalan_santri_ids = fields.One2many(
        'cdn.penilaian_quran_line',
        compute='_compute_riwayat_hafalan_santri',
        string='Riwayat Hafalan Santri',
        readonly=True
    )
    
    @api.depends('tahfidz_quran_ids', 'tahfidz_quran_ids.state', 'tahfidz_quran_ids.tahfidz_line_ids')
    def _compute_riwayat_hafalan_santri(self):
        for santri in self:
            if not santri.id:
                santri.riwayat_hafalan_santri_ids = False
                continue
            
            # Ambil semua penilaian quran yang sudah done untuk santri ini
            penilaian_ids = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', santri.id),
                ('state', '=', 'done')
            ]).ids
            
            # Ambil semua line dari penilaian tersebut
            riwayat_lines = self.env['cdn.penilaian_quran_line'].search([
                ('penilaian_id', 'in', penilaian_ids)
            ])
            
            santri.riwayat_hafalan_santri_ids = riwayat_lines

    def _compute_count_kesehatan(self):
        for siswa in self:
            siswa.kesehatan_count = self.env['cdn.kesehatan'].search_count([('siswa_id', '=', siswa.id)])
    def _compute_count_pelanggaran(self):
        for siswa in self:
            siswa.pelanggaran_count = self.env['cdn.pelanggaran'].search_count([('siswa_id', '=', siswa.id)])
    def _compute_count_prestasi(self):
        for siswa in self:
            siswa.prestasi_siswa_count = self.env['cdn.prestasi_siswa'].search_count([('siswa_id', '=', siswa.id)])
    # def _compute_count_tahfidz_quran(self):
    #     for siswa in self:
    #         siswa.tahfidz_quran_count = self.env['cdn.tahfidz_quran'].search_count([('siswa_id', '=', siswa.id)])

    # def _compute_count_penilaian_quran(self):
    #     for siswa in self:
    #         siswa.penilaian_quran_count = self.env['cdn.penilaian_quran'].search_count([
    #             ('siswa_id', '=', siswa.id)
    #         ])
    def _compute_count_penilaian_quran(self):
        for siswa in self:
            # Hitung berdasarkan penilaian_quran_line yang statusnya done
            penilaian_ids = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', siswa.id),
                ('state', '=', 'done')
            ]).ids
            
            siswa.penilaian_quran_count = self.env['cdn.penilaian_quran_line'].search_count([
                ('penilaian_id', 'in', penilaian_ids)
            ])
    @api.depends('tahfidz_quran_ids.state', 'tahfidz_quran_ids.tanggal')
    def _compute_tahfidz_terakhir(self):
        for siswa in self:
            last = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', siswa.id),
                ('state', '=', 'done')
            ], order='tanggal desc, id desc', limit=1)
            siswa.tahfidz_terakhir_id = last.id if last else False
    def action_confirm(self):
        for rec in self:
            rec.state = 'done'
            rec._compute_last_tahfidz()
            if rec.siswa_id:
                rec.siswa_id._compute_tahfidz_terakhir()            

    def _compute_count_saldo_tagihan(self):
        for siswa in self:
            if siswa.partner_id:
                # Ambil semua tagihan yang terkait dengan partner siswa
                tagihan = self.env['account.move'].search([
                    ('partner_id', '=', siswa.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', 'in', ['posted'])  # tagihan dan kerugian tetap terhitung
                ])
                # Hitung sisa tagihan (amount_residual_signed)
                siswa.saldo_tagihan_count = sum(tagihan.mapped('amount_residual_signed'))
    
    @api.depends('halaqoh_ids')
    def _compute_penanggung_jawab_ids(self):
        for rec in self:
            rec.penanggung_jawab_ids = rec.halaqoh_ids.mapped('penanggung_jawab_id')
            
    @api.depends('halaqoh_ids')
    def _compute_pengganti_all_ids(self):
        for rec in self:
            rec.pengganti_all_ids = rec.halaqoh_ids.mapped('pengganti_ids')
    def _compute_count_uang_saku(self):
        for siswa in self:
            if siswa.partner_id:
                uang_saku = self.env['cdn.uang_saku'].search([('siswa_id', '=', siswa.partner_id.id), ('state', '=', 'confirm')])
                print(uang_saku)
                siswa.uang_saku_count = sum(uang_saku.mapped('amount_in')) - sum(uang_saku.mapped('amount_out'))

    @api.depends('saldo_tagihan_count')
    def _compute_saldo_tagihan_formatted(self):
        for record in self:
            record.saldo_tagihan_formatted = int(record.saldo_tagihan_count)

    @api.depends('uang_saku_count')
    def _compute_uang_saku_formatted(self):
        for record in self:
            record.uang_saku_formatted = int(record.uang_saku_count)
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.halaqoh_id and rec.halaqoh_id not in rec.halaqoh_ids:
            rec.halaqoh_ids = [(4, rec.halaqoh_id.id)]
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.halaqoh_id and rec.halaqoh_id not in rec.halaqoh_ids:
                rec.halaqoh_ids = [(4, rec.halaqoh_id.id)]
        return res
    # actions smart button
    # def action_saldo_tagihan(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Tagihan Santri',
    #         'res_model': 'account.move',
    #         'view_mode': 'list,form',
    #         'target': 'current',
    #         'context': {
    #             'default_siswa_id': self.id,
    #             'default_partner_id': self.partner_id.id,
    #             'default_move_type': 'out_invoice',
    #             'search_default_filter_by_blm_lunas': 1,
    #         },
    #         'domain': [
    #             ('partner_id', '=', self.partner_id.id),
    #             ('move_type', '=', 'out_invoice'),
    #         ],
    #     }


    def action_saldo_tagihan(self):
            self.ensure_one()
            
            return {
                'name': f'Tagihan {self.partner_id.name}',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'views': [
                    (self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_tree').id, 'list'),
                    (self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_form').id, 'form'),
                ],
                'search_view_id': self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_search').id,
                'domain': [
                    ('partner_id', '=', self.partner_id.id), 
                    ('move_type', '=', 'out_invoice')
                ],
                'context': {
                    'default_move_type': 'out_invoice',
                    'default_partner_id': self.partner_id.id,
                    'default_siswa_id': self.id,
                    'search_default_filter_by_blm_lunas': 1,
                    # Pastikan form view menggunakan view yang benar
                    'form_view_ref': 'pesantren_keuangan.pesantren_tagihan_keuangan_view_form',
                    'tree_view_ref': 'pesantren_keuangan.pesantren_tagihan_keuangan_view_tree',
                },
                'target': 'current',
            }



    # def action_saldo_tagihan(self):

    #     self.ensure_one()

    #     base_action = self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_action').sudo().read()[0]

    #     return {
    #         'name': f'Tagihan {self.partner_id.name}',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.move',
    #         'view_mode': 'list,form',
    #         'views': base_action.get('views', []),  # Menggunakan views dari action custom
    #         'view_id': base_action.get('view_id', False),  # View ID utama
    #         'domain': [
    #             ('partner_id', '=', self.partner_id.id), 
    #             ('move_type', '=', 'out_invoice')
    #         ],
    #         'context': {
    #             # 'default_santri_id': self.id,
    #             'search_default_filter_by_blm_lunas': 1,
    #         },
    #     }

        # return {
        #     'name': 'Tagihan Santri',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'account.move',
        #     'view_mode': 'list,form',
        #     'domain': [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice')],
        #     'context': {
        #         'default_santri_id': self.id,
        #         'search_default_filter_by_blm_lunas': 1,
        #     },
        # }
        # self.ensure_one()
        # action = self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_action').sudo().read()[0]
        # action['domain'] = [
        #     ('partner_id', '=', self.partner_id.id),
        #     ('move_type', '=', 'out_invoice'),
        # ]
        # action['context'] = {
        #     'default_siswa_id': self.id,
        #     'default_partner_id': self.partner_id.id,
        #     'default_move_type': 'out_invoice',
        #     'search_default_filter_by_blm_lunas': 1,
        #     'use_search_default_filter_by_blm_lunas': True,
        # }
        # return action


    # def action_saldo_tagihan(self):
    #     self.ensure_one()
    #     action = self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_action').read()[0]
        
    #     # Use permanent domain filters instead of context-based filters
    #     action['domain'] = [
    #         ('partner_id', '=', self.partner_id.id),
    #         ('move_type', '=', 'out_invoice'),
    #         # Add this line to make the "Belum Lunas" filter permanent in the domain
    #         ('payment_state', 'in', ['not_paid', 'partial'])
    #         ('state', 'in', ['posted', 'kerugian']),
    #     ]
        
    #     action['context'] = {
    #         'default_siswa_id': self.id,
    #         'default_partner_id': self.partner_id.id,
    #         'default_move_type': 'out_invoice',
    #         # Keep this for initial filtering, but now we have a permanent domain filter too
    #         'search_default_filter_by_blm_lunas': 1,
    #     }
        
    #     return action



    def action_kesehatan(self):
        return {
            'name': 'Kesehatan',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.kesehatan',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }
    def action_pelanggaran(self):
        return {
            'name': 'Pelanggaran',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.pelanggaran',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }

    # def action_open_custom_wizard(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'custom_pin_popup',
    #         'name': 'Change PIN',
    #         'params': {
    #             'record_id': self.id,
    #             'model': self._name,
    #         }
    #     }

    # def action_open_custom_wizard(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'custom_pin_popup',
    #         'name': 'Change PIN',
    #         'params': {
    #             'model': 'res.partner.change.pin',
    #             'partner_id': self.partner_id.id,
    #         }
    #     }

    def action_open_custom_wizard(self):
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError("Santri tidak memiliki partner yang terkait!")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'custom_pin_popup',
            'name': 'Change PIN',
            'params': {
                'model': 'res.partner.change.pin',
                'partner_id': self.partner_id.id,
                'context': {'active_id': self.id, 'active_model': 'cdn.siswa'}
            }
        }

    def action_open_custom_wizard_cuy(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'custom_saldo_santri_wizard', 
            'name': 'Wizard Saldo Santri',
            'target': 'new', 
            'params': {
                'model': 'cdn.siswa',  
                'partner_id': self.partner_id.id,
                'santri_id': self.id,
                'context': {
                    'active_id': self.id, 
                    'active_model': 'cdn.siswa'
                }
            }
        }

    
    def action_prestasi_siswa(self):
        return {
            'name': 'Prestasi',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.prestasi_siswa',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }
    # def action_tahfidz_quran(self):
    #     return {
    #         'name': 'Tahfidz Quran',
    #         'view_type': 'form',
    #         'view_mode': 'list,form',
    #         'res_model': 'cdn.tahfidz_quran',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'context': {
    #             'default_siswa_id': self.id,
    #         },
    #         'domain': [('siswa_id', '=', self.id)]
    #     }
    # def action_tahfidz_quran(self):
    #     return {
    #         'name': 'Tahfidz Quran',
    #         'view_type': 'form',
    #         'view_mode': 'list,form',
    #         'res_model': 'cdn.penilaian_quran',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'context': {
    #             'default_siswa_id': self.id,
    #         },
    #         'domain': [('siswa_id', '=', self.id)]
    #     }
    def action_tahfidz_quran(self):
        self.ensure_one()
        
        # Ambil semua penilaian yang sudah done untuk santri ini
        penilaian_ids = self.env['cdn.penilaian_quran'].search([
            ('siswa_id', '=', self.id),
            ('state', '=', 'done')
        ]).ids
        
        return {
            'name': f'Tahfidz Al-Quran - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.penilaian_quran_line',
            'view_mode': 'list,form',
            'target': 'current',
            'views': [
                (self.env.ref('pesantren_kesantrian.view_penilaian_quran_line_tree').id, 'list'),
                (self.env.ref('pesantren_kesantrian.view_penilaian_quran_line_form').id, 'form'),
            ],
            'search_view_id': self.env.ref('pesantren_kesantrian.view_penilaian_quran_line_search').id,
            'domain': [('penilaian_id', 'in', penilaian_ids)],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
        }

    # def action_saldo_tagihan(self):
    #     return {
    #         'name': 'Saldo Tagihan',
    #         'view_mode': 'list,form',
    #         'res_model': 'account.move',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'context': {'default_partner_id': self.partner_id.id, 'default_move_type': 'out_invoice'},
    #         'domain': [('partner_id', '=', self.partner_id.id),('move_type', '=', 'out_invoice')]
    #     }

    def action_uang_saku(self):
        return {
            'name': 'Uang Saku',
            'view_mode': 'list,form',
            'res_model': 'cdn.uang_saku',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_siswa_id': self.partner_id.id},
            'domain': [('siswa_id', '=', self.partner_id.id)]
        }
        
    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None):
    #     domain = domain or []
    #     user = self.env.user
    #     context = self.env.context

    #     # 1. Superuser & Manager → Full
    #     if self.env.uid == SUPERUSER_ID or user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
    #         return super()._search(domain, offset, limit, order)

    #     is_guru_quran   = user.has_group('pesantren_guruquran.group_guru_quran_staff')
    #     is_guru         = user.has_group('pesantren_guru.group_guru_staff')
    #     is_musyrif      = user.has_group('pesantren_musyrif.group_musyrif_staff')

    #     # 2. DETEKSI CONTEXT - Perbaikan di sini
    #     from_guru_quran = bool(
    #         context.get('from_guru_quran') or
    #         context.get('active_model') in ['cdn.absen_halaqoh', 'cdn.penilaian_quran', 'cdn.halaqoh', 'cdn.penilaian_quran_line', 'cdn.absen_halaqoh_line']
    #     )
    #     from_musyrif = bool(
    #         context.get('from_musyrif') or
    #         context.get('active_model') in ['cdn.absen_musyrif', 'cdn.kegiatan_musyrif']
    #     )

    #     # 4. MUSYRIF + CONTEXT → FILTER KAMAR
    #     if is_musyrif and from_musyrif:
    #         domain += [
    #             '|',
    #             ('kamar_id.musyrif_id.user_id', '=', user.id),
    #             ('kamar_id.pengganti_ids.user_id', '=', user.id)
    #         ]
    #         return super()._search(domain, offset, limit, order)
        
    #     # 3. GURU QURAN dan Akademik → FULL ACCESS (tidak perlu cek context lagi)
    #     if is_guru_quran or is_guru:
    #         # Guru Quran selalu punya akses penuh ke siswa
    #         return super()._search(domain, offset, limit, order)

    #     # 5. MUSYRIF ONLY → FILTER
    #     if is_musyrif:
    #         domain += [
    #             '|',
    #             ('kamar_id.musyrif_id.user_id', '=', user.id),
    #             ('kamar_id.pengganti_ids.user_id', '=', user.id)
    #         ]
    #         return super()._search(domain, offset, limit, order)

    #     # 6. DEFAULT: FULL
    #     return super()._search(domain, offset, limit, order)
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        domain = domain or []
        user = self.env.user
        context = self.env.context

        # 1. Superuser & Manager → Full
        if self.env.uid == SUPERUSER_ID or user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return super()._search(domain, offset, limit, order)

        is_guru_quran = user.has_group('pesantren_guruquran.group_guru_quran_staff')
        is_guru       = user.has_group('pesantren_guru.group_guru_staff')
        is_musyrif    = user.has_group('pesantren_musyrif.group_musyrif_staff')

        # 2. DETEKSI CONTEXT
        from_guru_quran = bool(
            context.get('from_guru_quran') or
            context.get('active_model') in [
                'cdn.absen_halaqoh', 'cdn.penilaian_quran', 'cdn.halaqoh',
                'cdn.penilaian_quran_line', 'cdn.absen_halaqoh_line'
            ]
        )
        from_musyrif = bool(
            context.get('from_musyrif') or
            context.get('active_model') in ['cdn.absen_musyrif', 'cdn.kegiatan_musyrif']
        )

        # MUSYRIF + CONTEXT → FILTER KAMAR
        if is_musyrif and from_musyrif:
            domain += [
                '|',
                ('kamar_id.musyrif_id.user_id', '=', user.id),
                ('kamar_id.pengganti_ids.user_id', '=', user.id)
            ]
            return super()._search(domain, offset, limit, order)
        
        if is_guru_quran or is_guru:
            return super()._search(domain, offset, limit, order)

        # DEFAULT: FULL (untuk role lain)
        return super()._search(domain, offset, limit, order)
