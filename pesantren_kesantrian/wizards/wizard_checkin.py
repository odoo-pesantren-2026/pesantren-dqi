from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)


class PerijinanCheckIn(models.TransientModel):
    _name           = 'cdn.perijinan.checkin'
    _description    = 'CheckIn Perijinan Santri'

    tgl_ijin     = fields.Datetime(string='Tgl Ijin', required=True, default=lambda self: fields.Datetime.now())
    siswa_id     = fields.Many2one('cdn.siswa', string='Siswa', required=True , ondelete='cascade')
    perijinan_id = fields.Many2one('cdn.perijinan', string='Perijinan', required=False)
    kelas_id     = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True)
    kamar_id     = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id   = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id   = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    keperluan    = fields.Many2one(string='Keperluan', related='perijinan_id.keperluan', readonly=False)
    lama_ijin    = fields.Char(string='Lama Ijin', related='perijinan_id.lama_ijin', readonly=True)
    tgl_kembali  = fields.Datetime(string='Tgl Kembali', related='perijinan_id.tgl_kembali', readonly=False, default=lambda self: fields.Datetime.now() + relativedelta(days=1))
    penjemput    = fields.Char(string='Penjemput', related='perijinan_id.penjemput', readonly=False)

    barcode = fields.Char(string='Kartu Santri',readonly=False)
 
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Mengisi siswa_id berdasarkan barcode yang diinput"""
        _logger.info(f"Cek Barcode: {self.barcode}")
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
            _logger.exception(f"Data Santri: {siswa}")

            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False 
                kartu_sementara = self.barcode
                self.barcode = False
                return {
                    'warning' : {
                        'title' : 'Perhatian !',
                        'message' : f"Tidak dapat menemukan kartu santri dengan kode {kartu_sementara}"
                    }
                }
                

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            Perijinan = self.env['cdn.perijinan'].search([('siswa_id', '=', self.siswa_id.id), ('state', '=', 'Permission')], limit=1)
           
            if not Perijinan:
                raise UserError('Tidak ada perijinan keluar untuk santri ini, Silakan di cek kembali!')
            
            self.perijinan_id = Perijinan.id
            

    def action_return(self):
        """Santri kembali ke pesantren"""
        for rec in self:
            rec.waktu_kembali = fields.Datetime.now()

            # Jangan ubah tgl_kembali dari perijinan
            # if not rec.waktu_keluar:
            #     rec.tgl_kembali = rec.tgl_ijin

            # Hitung terlambat atau tepat waktu
            if rec.waktu_kembali and rec.tgl_kembali:
                if rec.waktu_kembali > rec.tgl_kembali:
                    # Terlambat
                    rec.state = 'Overdue'
                    delta = rec.waktu_kembali - rec.tgl_kembali
                    total_menit = int(delta.total_seconds() / 60)
                    hari = total_menit // (24 * 60)
                    sisa_menit = total_menit % (24 * 60)
                    jam = sisa_menit // 60
                    menit = sisa_menit % 60
                    rec.jatuh_tempo = f"{hari} hari {jam} jam {menit} menit"
                    rec.cek_terlambat = True
                    rec.is_bukti_submitted = False
                    rec.message_post(
                        body=f"Santri {rec.siswa_id.name} kembali terlambat pada {rec.waktu_kembali.strftime('%d-%m-%Y %H:%M')}. Musyrif diminta upload bukti dan keterangan."
                    )
                else:
                    # Tepat waktu
                    rec.state = 'Return'
                    rec.jatuh_tempo = "0 hari 0 jam 0 menit"
                    rec.cek_terlambat = False
                    
    def action_checkin(self):
        """Proses check-in santri"""
        if not self.perijinan_id:
            raise UserError("Santri belum dipilih.")
        
        perijinan = self.perijinan_id
        waktu_kembali_sekarang = fields.Datetime.now()

        perijinan.write({
            'waktu_kembali': waktu_kembali_sekarang
        })

        # Panggil action_return di perijinan untuk logika terlambat otomatis
        perijinan.action_return()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.perijinan',
            'view_mode': 'form',
            'res_id': perijinan.id,
            'target': 'current',
        }
    
    @api.depends('tgl_ijin', 'tgl_kembali')
    def _compute_lama_ijin(self):
        for record in self:
            if record.tgl_ijin and record.tgl_kembali:
                # Hitung selisih waktu
                delta = record.tgl_kembali - record.tgl_ijin
                
                # Hitung hari, jam, dan menit
                total_menit = int(delta.total_seconds() / 60)
                hari = total_menit // (24 * 60)
                sisa_menit = total_menit % (24 * 60)
                jam = sisa_menit // 60
                menit = sisa_menit % 60
                
                # Format string untuk menampilkan hari, jam, menit
                record.lama_ijin = f"{hari} hari {jam} jam {menit} menit"