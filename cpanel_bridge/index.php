<?php
// ============================================================
// ZKTeco HTTP-to-HTTPS Proxy Bridge for Render
// Forwards plain HTTP requests from older ZKTeco devices to Render
// ============================================================

$render_host = 'https://attendance-easytime-1.onrender.com';
$request_uri = $_SERVER['REQUEST_URI'];
$target_url  = $render_host . $request_uri;

$ch = curl_init($target_url);

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$headers = [];
if (!empty($_SERVER['CONTENT_TYPE'])) {
    $headers[] = 'Content-Type: ' . $_SERVER['CONTENT_TYPE'];
}

if ($method === 'POST') {
    $body = file_get_contents('php://input');
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    $headers[] = 'Content-Length: ' . strlen($body);
}

if (!empty($headers)) {
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
}

$response     = curl_exec($ch);
$http_code    = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);

if (curl_errno($ch)) {
    http_response_code(502);
    header('Content-Type: text/plain');
    echo 'Proxy error: ' . curl_error($ch);
    curl_close($ch);
    exit;
}

curl_close($ch);

http_response_code($http_code ?: 200);
header('Content-Type: ' . ($content_type ?: 'text/plain'));
echo $response;
