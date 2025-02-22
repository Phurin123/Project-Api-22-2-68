// ฟังก์ชันสำหรับอัปโหลดภาพ
async function uploadImage() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';

  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultText = document.getElementById('resultText');
    const imagePreview = document.getElementById('imagePreview');
    const processedImage = document.getElementById('processedImage');

    loadingSpinner.style.display = 'block';
    resultText.textContent = '';
    processedImage.style.display = 'none';

    const reader = new FileReader();
    reader.onload = () => {
      imagePreview.src = reader.result;
      imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    try {
      const response = await fetch('http://127.0.0.1:5000/analyze-image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      loadingSpinner.style.display = 'none';

      if (response.ok) {
        // ตรวจสอบสถานะ
        if (data.status === 'failed') {
          resultText.textContent = 'ผลลัพธ์: ไม่ผ่าน';
          resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดง
        } else if (data.status === 'passed') {
          resultText.textContent = 'ผลลัพธ์: ผ่าน';
          resultText.style.color = 'green'; // เปลี่ยนสีเป็นเขียว
        }

        if (data.processed_image_url) {
          processedImage.src = data.processed_image_url;
          processedImage.style.display = 'block';
        }
      } else {
        resultText.textContent = `ข้อผิดพลาด: ${data.error || 'เกิดข้อผิดพลาด'}`;
        resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดงเมื่อเกิดข้อผิดพลาด
      }
    } catch (error) {
      loadingSpinner.style.display = 'none';
      resultText.textContent = 'ข้อผิดพลาด: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์';
      resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดงเมื่อเกิดข้อผิดพลาด
    }
  };

  input.click();
}

// ฟังก์ชันขอ API Key
function requestApiKey() {
  const email = prompt('กรุณาใส่อีเมลของคุณเพื่อขอ API Key:');
  if (!email) return;

  fetch('http://127.0.0.1:5000/request-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
    .then((response) => response.json())
    .then((data) => {
      alert(data.apiKey ? `API Key ของคุณคือ: ${data.apiKey}` : `ข้อผิดพลาด: ${data.error}`);
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันรายงานปัญหา
function reportIssue() {
  const issueDescription = prompt('กรุณาระบุรายละเอียดปัญหาที่คุณพบ:');
  if (!issueDescription) return;

  fetch('http://127.0.0.1:5000/report-issue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ issue: issueDescription }),
  })
    .then((response) => response.json())
    .then((data) => {
      alert(data.success ? 'ขอบคุณสำหรับการรายงานปัญหาของคุณ!' : 'ไม่สามารถส่งข้อมูลได้ กรุณาลองใหม่อีกครั้ง');
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันสำหรับดาวน์โหลดเอกสารคู่มือ
function downloadManual() {
  const url = "https://example.com/path/to/manual.pdf"; // แก้ไขให้เป็นพาธของไฟล์เอกสารที่คุณเตรียมไว้
  const link = document.createElement('a');
  link.href = url;
  link.download = 'คู่มือการใช้งาน.pdf'; // ชื่อไฟล์ที่ผู้ใช้จะดาวน์โหลด
  link.click();
}