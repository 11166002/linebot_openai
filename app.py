const kanaList = [
  {
    kana: "あ",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7).m4a"
  },
  {
    kana: "い",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)1.m4a"
  },
  {
    kana: "う",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)2.m4a"
  },
  {
    kana: "え",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)3.m4a"
  },
  {
    kana: "お",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)4.m4a"
  },
  {
    kana: "か",
    audio: "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)5.m4a"
  }
];

let currentKana = null;

function nextQuestion() {
  const q = kanaList[Math.floor(Math.random() * kanaList.length)];
  currentKana = q.kana;
  document.getElementById("question").innerText = q.kana;

  const audio = document.getElementById("audio");
  audio.src = q.audio;
  audio.play();

  clearCanvas();
}

function clearCanvas() {
  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  document.getElementById("result").innerText = "";
}

function sendImage() {
  if (!currentKana) {
    alert("請先點『下一題』！");
    return;
  }

  const canvas = document.getElementById("canvas");
  const imageData = canvas.toDataURL("image/png");

  fetch("https://你的-render-url/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image: imageData,
      answer: currentKana
    })
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById("result").innerText =
        data.correct
          ? `✅ 答對了！（分數：${data.score}）`
          : `❌ 錯了喔～（分數：${data.score}）`;
    })
    .catch(err => {
      console.error(err);
      alert("❌ 發生錯誤，請稍後再試");
    });
}

// 畫圖邏輯
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let drawing = false;

canvas.addEventListener("mousedown", () => drawing = true);
canvas.addEventListener("mouseup", () => {
  drawing = false;
  ctx.beginPath();
});
canvas.addEventListener("mousemove", draw);

canvas.addEventListener("touchstart", e => {
  drawing = true;
  drawTouch(e);
});
canvas.addEventListener("touchend", () => {
  drawing = false;
  ctx.beginPath();
});
canvas.addEventListener("touchmove", drawTouch);

function draw(e) {
  if (!drawing) return;
  const rect = canvas.getBoundingClientRect();
  ctx.lineWidth = 4;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#000";
  ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
}

function drawTouch(e) {
  if (!drawing) return;
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  ctx.lineWidth = 4;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#000";
  ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(touch.clientX - rect.left, touch.clientY - rect.top);
}
