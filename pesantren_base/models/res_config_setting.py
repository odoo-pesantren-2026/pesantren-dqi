# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    center_latitude = fields.Float(string='Center Latitude', default=-6.200000)
    center_longitude = fields.Float(
        string='Center Longitude', default=106.816666)
    acceptable_radius = fields.Integer(
        string='Acceptable Radius (meters)', default=1000)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'attendance.center_latitude', self.center_latitude)
        self.env['ir.config_parameter'].sudo().set_param(
            'attendance.center_longitude', self.center_longitude)
        self.env['ir.config_parameter'].sudo().set_param(
            'attendance.acceptable_radius', self.acceptable_radius)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            center_latitude=float(self.env['ir.config_parameter'].sudo().get_param(
                'attendance.center_latitude', default=-6.200000)),
            center_longitude=float(self.env['ir.config_parameter'].sudo().get_param(
                'attendance.center_longitude', default=106.816666)),
            acceptable_radius=int(self.env['ir.config_parameter'].sudo(
            ).get_param('attendance.acceptable_radius', default=1000)),
        )
        return res

    @api.model
    def action_set_current_location(self):
        """
        Dummy method to be called via button.
        """
        # Metode ini akan dipicu dari JavaScript untuk menangkap lokasi pengguna
        pass


class InheritAttendance(models.Model):
    _inherit = 'hr.attendance'

    image_1920 = fields.Binary(string='Bukti Foto')

    def action_check_location(self):
        """
        Memeriksa apakah lokasi pengguna berada dalam radius yang dapat diterima.
        """
        # Mengambil parameter konfigurasi untuk titik pusat dan radius
        config = self.env['ir.config_parameter'].sudo()
        center_lat = float(config.get_param(
            'attendance.center_latitude', default=-6.200000))
        center_long = float(config.get_param(
            'attendance.center_longitude', default=106.816666))
        radius = float(config.get_param(
            'attendance.acceptable_radius', default=1000))

        for record in self:
            # Pastikan data geolokasi ada
            if not record.in_latitude or not record.in_longitude:
                raise UserError(
                    _("Lokasi tidak ditemukan. Pastikan perangkat Anda mengaktifkan GPS."))

            # Cek apakah gambar sudah disisipkan
            if not record.image_1920:
                raise UserError(
                    _("Bukti gambar wajib disisipkan untuk absensi."))

            # Hitung jarak (Haversine Formula)
            distance = self._compute_distance(
                record.in_latitude, record.in_longitude, center_lat, center_long)
            if distance > radius:
                record.write({'overtime_status': 'refused'})
                raise UserError(
                    _("Absensi dilakukan di luar radius yang diizinkan. Absensi ditolak mohon ulangi absensi."))

            # Mengubah status absensi menjadi diterima
            record.write({'overtime_status': 'approved'})

    def action_cancel_attendance(self):
        """
        Membatalkan absensi dengan langsung mengubah status.
        """
        for record in self:
            record.write({'overtime_status': 'refused'})

    def action_approv_attendance(self):
        """
        Membatalkan absensi dengan langsung mengubah status.
        """
        for record in self:
            record.write({'overtime_status': 'approved'})

    @staticmethod
    def _compute_distance(lat1, lon1, lat2, lon2):
        """
        Menghitung jarak menggunakan formula Haversine.
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Radius bumi dalam meter
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        delta_phi = radians(lat2 - lat1)
        delta_lambda = radians(lon2 - lon1)

        a = sin(delta_phi / 2) ** 2 + cos(phi1) * \
            cos(phi2) * sin(delta_lambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c
