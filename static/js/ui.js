window.showToast = (msg, icon="success") => {
  Swal.fire({icon, title: msg, timer: 1400, showConfirmButton:false});
};
window.confirmDialog = (title, text, confirmText="確認") => {
  return Swal.fire({title, text, icon:"question", showCancelButton:true, confirmButtonText:confirmText});
};
