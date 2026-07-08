const API_URL = "https://inuyasha-character-match.onrender.com/match";

const imageInput = document.getElementById("imageInput");
const uploadArea = document.getElementById("uploadArea");
const selectBtn = document.getElementById("selectBtn");
const previewImage = document.getElementById("previewImage");
const emptyPreview = document.getElementById("emptyPreview");
const analyzeBtn = document.getElementById("analyzeBtn");
const loadingSection = document.getElementById("loadingSection");
const resultSection = document.getElementById("resultSection");
const resultCards = document.getElementById("resultCards");
const retryBtn = document.getElementById("retryBtn");

let selectedBase64 = "";

uploadArea.addEventListener("click", () => {
  imageInput.click();
});

selectBtn.addEventListener("click", (event) => {
  event.stopPropagation();
  imageInput.click();
});

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (!file) return;

  const reader = new FileReader();

  reader.onload = () => {
    selectedBase64 = reader.result;

    previewImage.src = selectedBase64;
    previewImage.style.display = "block";
    emptyPreview.style.display = "none";

    analyzeBtn.disabled = false;
  };

  reader.readAsDataURL(file);
});

analyzeBtn.addEventListener("click", async () => {
  if (!selectedBase64) {
    alert("사진을 먼저 선택해주세요!");
    return;
  }

  loadingSection.classList.remove("hidden");
  resultSection.classList.add("hidden");
  resultCards.innerHTML = "";

  analyzeBtn.disabled = true;
  analyzeBtn.querySelector("strong").innerText = "분석중...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        image_base64: selectedBase64
      })
    });

    if (!response.ok) {
      throw new Error("API 요청 실패");
    }

    const data = await response.json();

    const results =
      data.results ||
      data.top3 ||
      data.matches ||
      data.result ||
      [];

    renderResults(results.slice(0, 3));
  } catch (error) {
    console.error(error);
    alert("분석 실패 😭 백엔드가 켜져있는지 확인해줘!");
  } finally {
    loadingSection.classList.add("hidden");
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector("strong").innerText = "분석하기";
  }
});

function renderResults(results) {
  resultCards.innerHTML = "";

  results.forEach((item, index) => {
    const name = item.name || item.character || item.character_name || "이누야샤 캐릭터";
    const image = item.image_url || item.image || "";
    const percent = item.percent || item.score || item.match_percent || 90;
    const reason = item.reason || item.description || "분위기와 인상이 비슷하게 분석됐어요.";
    const keywordsText = item.keywords || item.face_tags || "";

    const safePercent = getPercentNumber(percent);
    const stars = getStars(safePercent);
    const crown = index === 0 ? "👑" : index === 1 ? "🥈" : "🥉";

    const keywords = String(keywordsText)
      .split(",")
      .map((word) => word.trim())
      .filter(Boolean)
      .slice(0, 4);

    const card = document.createElement("article");
    card.className = "result-card";

    card.innerHTML = `
      <div class="result-rank">${crown} TOP ${index + 1}</div>

      <div class="result-image-wrap">
        <div class="crown">${crown} ${safePercent}% MATCH</div>
        ${
          image
            ? `<img src="${image}" alt="${name}" />`
            : `<div class="result-placeholder">🐾</div>`
        }
      </div>

      <div class="result-content">
        <h3>${name}</h3>

        <div class="stars">${stars}</div>

        <span class="percent">${safePercent}% 일치</span>

        <div class="percent-bar">
          <div class="percent-fill" style="width:${safePercent}%"></div>
        </div>

        <p class="reason">${reason}</p>

        ${
          keywords.length > 0
            ? `<div class="keyword-list">
                ${keywords.map((word) => `<span class="keyword">🏷 ${word}</span>`).join("")}
              </div>`
            : ""
        }
      </div>
    `;

    resultCards.appendChild(card);
  });

  resultSection.classList.remove("hidden");
  resultSection.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

function getPercentNumber(value) {
  if (typeof value === "number") {
    if (value <= 1) return Math.round(value * 100);
    return Math.round(value);
  }

  const number = parseInt(String(value).replace("%", ""), 10);
  return Number.isNaN(number) ? 90 : number;
}

function getStars(percent) {
  if (percent >= 90) return "★★★★★";
  if (percent >= 82) return "★★★★☆";
  if (percent >= 74) return "★★★☆☆";
  return "★★★☆☆";
}

function formatPercent(value) {
  if (typeof value === "number") {
    if (value <= 1) return `${Math.round(value * 100)}%`;
    return `${Math.round(value)}%`;
  }

  const text = String(value);
  return text.includes("%") ? text : `${text}%`;
}

retryBtn.addEventListener("click", () => {
  selectedBase64 = "";
  imageInput.value = "";

  previewImage.src = "";
  previewImage.style.display = "none";
  emptyPreview.style.display = "block";

  analyzeBtn.disabled = true;
  resultSection.classList.add("hidden");
  resultCards.innerHTML = "";

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});
