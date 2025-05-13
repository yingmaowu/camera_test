<?php
$data = json_decode(file_get_contents("php://input"), true);
$image = $data['image'];
$patient = $data['patient'];

if (!$image || !$patient) {
  http_response_code(400);
  echo "缺少影像或病人ID";
  exit;
}

// 建立資料夾
$folder = "uploads/" . $patient;
if (!file_exists($folder)) {
  mkdir($folder, 0777, true);
}

// 儲存圖片
$imageData = explode(",", $image)[1];  // 去掉 data:image/png;base64,...
$imageBinary = base64_decode($imageData);
$filename = $folder . "/tongue_" . date("YmdHis") . ".png";
file_put_contents($filename, $imageBinary);

echo "儲存成功：" . basename($filename);
?>
