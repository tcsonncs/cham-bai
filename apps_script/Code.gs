/**
 * Kho dữ liệu cho app Chấm bài Toán.
 *
 * Dán toàn bộ tệp này vào Apps Script của một trang tính Google, thay dòng
 * TOKEN bên dưới bằng mã riêng (lấy trong hướng dẫn), rồi Triển khai dạng
 * Ứng dụng web.
 */

var TOKEN = 'THAY_TOKEN_VAO_DAY';

var COT = {
  dot_cham: ['id', 'ten', 'lop', 'cap_hoc', 'ngay_tao', 'de_bai', 'dap_an', 'rubric'],
  hoc_sinh: ['id', 'dot_id', 'ho_ten', 'ma_hs'],
  bai_lam: ['id', 'dot_id', 'hs_id', 'anh', 'text_doc', 'text_chot',
            'trac_nghiem', 'ket_qua', 'tong_goi_y', 'tong_chot',
            'trang_thai', 'ngay_tao', 'ngay_cham']
};

function doGet(e) {
  return tra({ok: true, chao: 'Kho Cham bai Toan'});
}

function doPost(e) {
  var khoa = LockService.getScriptLock();
  try {
    khoa.waitLock(30000);
    var goi = JSON.parse(e.postData.contents);
    if (goi.token !== TOKEN) {
      return tra({ok: false, loi: 'sai token'});
    }
    if (goi.action === 'doc') {
      return tra({ok: true, du_lieu: docTatCa()});
    }
    if (goi.action === 'ghi') {
      ghiBang(goi.sheet, goi.rows || []);
      return tra({ok: true});
    }
    // Ảnh bài làm lưu thành file trong thư mục Drive riêng, không mất khi
    // máy chủ Streamlit khởi động lại.
    if (goi.action === 'luu_anh') {
      return tra({ok: true, id: luuAnh(goi.ten, goi.b64)});
    }
    if (goi.action === 'lay_anh') {
      var b64 = layAnh(goi.ten);
      return tra(b64 === null ? {ok: true, co: false}
                              : {ok: true, co: true, b64: b64});
    }
    if (goi.action === 'xoa_anh') {
      xoaAnh(goi.ten);
      return tra({ok: true});
    }
    return tra({ok: false, loi: 'action khong ho tro: ' + goi.action});
  } catch (loi) {
    return tra({ok: false, loi: String(loi)});
  } finally {
    khoa.releaseLock();
  }
}

var THU_MUC_ANH = 'ChamBaiToan_Anh';

function thuMucAnh() {
  var it = DriveApp.getFoldersByName(THU_MUC_ANH);
  return it.hasNext() ? it.next() : DriveApp.createFolder(THU_MUC_ANH);
}

function timAnh(ten) {
  var it = thuMucAnh().getFilesByName(ten);
  return it.hasNext() ? it.next() : null;
}

function luuAnh(ten, b64) {
  var cu = timAnh(ten);
  if (cu) { cu.setTrashed(true); }
  var blob = Utilities.newBlob(Utilities.base64Decode(b64), 'image/jpeg', ten);
  return thuMucAnh().createFile(blob).getId();
}

function layAnh(ten) {
  var f = timAnh(ten);
  return f ? Utilities.base64Encode(f.getBlob().getBytes()) : null;
}

function xoaAnh(ten) {
  var f = timAnh(ten);
  if (f) { f.setTrashed(true); }
}

function tra(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function layBang(ten) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(ten);
  if (!sh) {
    sh = ss.insertSheet(ten);
  }
  if (sh.getLastRow() === 0) {
    sh.appendRow(COT[ten]);
  }
  return sh;
}

function docTatCa() {
  var ketQua = {};
  for (var ten in COT) {
    var sh = layBang(ten);
    var giaTri = sh.getDataRange().getValues();
    var ds = [];
    if (giaTri.length > 1) {
      var dau = giaTri[0];
      for (var i = 1; i < giaTri.length; i++) {
        var dong = giaTri[i];
        if (dong.join('') === '') continue;
        var obj = {};
        for (var j = 0; j < dau.length; j++) {
          var v = dong[j];
          obj[dau[j]] = (v === '' || v === null) ? '' : v;
        }
        ds.push(obj);
      }
    }
    ketQua[ten] = ds;
  }
  return ketQua;
}

function ghiBang(ten, rows) {
  if (!COT[ten]) {
    throw new Error('khong co bang ' + ten);
  }
  var sh = layBang(ten);
  var cot = COT[ten];

  // Ghi qua getRange/setValues để chuỗi dài không bị hiểu là công thức.
  var duLieu = rows.map(function (r) {
    return cot.map(function (c) {
      var v = r[c];
      return (v === null || v === undefined) ? '' : String(v);
    });
  });

  sh.clearContents();
  sh.getRange(1, 1, 1, cot.length).setValues([cot]);
  if (duLieu.length) {
    sh.getRange(2, 1, duLieu.length, cot.length).setValues(duLieu);
  }
}
