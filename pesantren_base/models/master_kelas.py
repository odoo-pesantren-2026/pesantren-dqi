# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re


class master_kelas(models.Model):
    _name = "cdn.master_kelas"
    _description = "Tabel Data Master Kelas"
    _order = "tingkat_urutan, jurusan_id, nama_kelas, id"

    name = fields.Char(
        required=True, string="Nama Kelas", copy=False, readonly=True
    )
    jenjang = fields.Selection(
        selection=[
            ("paud", "PAUD"),
            ("tk", "TK/RA"),
            ("sd", "SD/MI"),
            ("smp", "SMP/MTS"),
            ("sma", "SMA/MA"),
            ("nonformal", "Non formal"),
            ("rtq", "Rumah Tahfidz Quran"),
        ],
        string="Jenjang",
        required=True,
    )
    tingkat = fields.Many2one(
        comodel_name="cdn.tingkat",
        string="Tingkat",
        required=True,
        domain="[('jenjang', '=', jenjang)]",
    )
    jurusan_id = fields.Many2one(
        comodel_name="cdn.master_jurusan", string="Jurusan / Peminatan"
    )
    nama_kelas = fields.Char(string="Nama Kelas")

    tingkat_urutan = fields.Integer(
        string="Urutan Tingkat",
        compute="_compute_tingkat_urutan",
        store=True,
        help="Urutan numerik tingkat untuk sorting",
    )

    # ===============================
    # Constraint unik
    # ===============================
    @api.constrains("name")
    def _check_unique_name(self):
        for record in self:
            if self.search_count([("name", "=", record.name)]) > 1:
                raise UserError(_("Master Data Kelas harus unik!"))

    # ===============================
    # Hitung urutan tingkat
    # ===============================
    @api.depends("tingkat", "jenjang")
    def _compute_tingkat_urutan(self):
        for record in self:
            urutan = 999
            if record.tingkat:
                tingkat_name = str(record.tingkat.name or "").strip().lower()

                if record.jenjang == "tk":
                    urutan = 1 if "a" in tingkat_name or "1" in tingkat_name else 2
                elif record.jenjang == "paud":
                    urutan = 1 if "a" in tingkat_name or "play" in tingkat_name else 2
                elif record.jenjang in ["sd", "smp", "sma"]:
                    numbers = re.findall(r"\d+", tingkat_name)
                    if numbers:
                        urutan = int(numbers[0])
                    else:
                        tingkat_mapping = {
                            "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6,
                            "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12,
                        }
                        for key, value in tingkat_mapping.items():
                            if key in tingkat_name:
                                urutan = value
                                break
            record.tingkat_urutan = urutan

    # ===============================
    # Helper konversi angka ke romawi
    # ===============================
    def _convert_to_roman(self, number):
        roman = [
            (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
        ]
        result = ""
        for value, letter in roman:
            while number >= value:
                result += letter
                number -= value
        return result

    # ===============================
    # Helper ambil nama dasar kelas
    # ===============================
    def _get_base_name(self, jenjang, tingkat):
        if not tingkat:
            return ""

        tingkat_name = str(tingkat.name or "").strip()

        if jenjang in ["paud", "tk"]:
            prefix = "PAUD" if jenjang == "paud" else "TK"

            # mapping angka → huruf
            mapping = {"1": "A", "2": "B"}
            tingkat_label = mapping.get(tingkat_name, tingkat_name)

            return f"{prefix} {tingkat_label}"

        elif jenjang in ["sd", "smp", "sma"]:
            try:
                return self._convert_to_roman(int(tingkat_name))
            except ValueError:
                return tingkat_name.upper()
        else:
            return tingkat_name.upper()

    # ===============================
    # Onchange → preview name
    # ===============================

    @api.onchange("tingkat", "jurusan_id", "nama_kelas")
    def onchange_tingkat_nama_kelas(self):
        if self.tingkat:
            base_name = self._get_base_name(self.jenjang, self.tingkat)

            if self.jurusan_id and self.nama_kelas:
                self.name = f"{base_name} - {self.jurusan_id.name} - {self.nama_kelas}"
            elif self.jurusan_id:
                self.name = f"{base_name} - {self.jurusan_id.name}"
            elif self.nama_kelas:
                self.name = f"{base_name} - {self.nama_kelas}"
            else:
                self.name = base_name

    # ===============================
    # Create override
    # ===============================
    @api.model
    def create(self, vals):
        tingkat = self.env["cdn.tingkat"].browse(vals["tingkat"])
        jenjang = vals.get("jenjang")

        base_name = self._get_base_name(jenjang, tingkat)

        name_parts = [base_name]
        if vals.get("jurusan_id"):
            jurusan = self.env["cdn.master_jurusan"].browse(vals["jurusan_id"])
            name_parts.append(jurusan.name)
        if vals.get("nama_kelas"):
            name_parts.append(vals["nama_kelas"])

        vals["name"] = " - ".join(name_parts)
        return super(master_kelas, self).create(vals)

    # ===============================
    # Write override
    # ===============================
    def write(self, vals):
        res = super(master_kelas, self).write(vals)

        if any(k in vals for k in ["tingkat", "jurusan_id", "nama_kelas", "jenjang"]):
            for record in self:
                base_name = record._get_base_name(
                    record.jenjang, record.tingkat)

                if record.jurusan_id and record.nama_kelas:
                    name = f"{base_name} - {record.jurusan_id.name} - {record.nama_kelas}"
                elif record.jurusan_id:
                    name = f"{base_name} - {record.jurusan_id.name}"
                elif record.nama_kelas:
                    name = f"{base_name} - {record.nama_kelas}"
                else:
                    name = base_name

                if name != record.name:
                    record.with_context(
                        no_name_update=True).write({"name": name})

        return res


class master_jurusan(models.Model):
    _name = "cdn.master_jurusan"
    _description = "Tabel Master Data Jurusan SMA"

    name = fields.Char(string="Nama Bidang/Jurusan", required=True)
    active = fields.Boolean(string="Aktif", default=True)
    keterangan = fields.Char(string="Keterangan")
