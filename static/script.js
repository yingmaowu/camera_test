document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const context = canvas.getContext("2d");
  let dataURL = "";

  // 啟動攝影機
  navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
      video.srcObject = stream;
      video.play();
    })
    .catch((err) => {
      console.error("❌ 鏡頭啟用錯誤:", err.name, err.message);
      alert("❌ 鏡頭啟動失敗：" + err.message);
    });

  // 拍照
  document.getElementById("snap").addEventListener("click", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    dataURL = canvas.toDataURL("image/png");
    alert("📸 拍照完成！");
  });

  // 上傳圖片
document.getElementById("upload").addEventListener("click", () => {
  if (!dataURL) {
    alert("請先拍照！");git add .
    return;
  }

  const patientId = document.getElementById("patientId").value.trim();
  if (!patientId) {
    alert("❗ 請輸入病人 ID");
    return;
  }

  fetch("upload.php", {
    method: "POST",
    body: JSON.stringify({ image: dataURL, patient: patientId }),
    headers: {
      "Content-Type": "application/json"
    }
  })
  .then(res => res.text())
  .then(msg => alert("✅ 上傳成功：" + msg))
  .catch(err => alert("❌ 上傳錯誤：" + err));
});

});
