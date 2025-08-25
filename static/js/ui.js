// 簡易通知
window.showToast = (msg, icon = "success") => {
  Swal.fire({ icon, title: msg, timer: 1400, showConfirmButton: false });
};

// 確認對話框
window.confirmDialog = (title, text, confirmText = "確認") => {
  return Swal.fire({
    title, text, icon: "question",
    showCancelButton: true, confirmButtonText: confirmText
  });
};
