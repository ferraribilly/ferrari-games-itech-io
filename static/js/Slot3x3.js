//CONFIGURAÇAO 3X3 COM TOTAL DE 15 IMAGENS
import Reel from "./Reel3x3.js";
import Symbol from "./Symbol3x3.js";

export default class Slot {
  constructor(domElement, config = {}) {
    Symbol.preload();

    this.balanceUI = document.getElementById("balance");
    this.betUI = document.getElementById("betValue");
    this.winUI = document.getElementById("win");
    this.espehoWinUI = document.getElementById("espeho_win");

    // >>> AUDIOS <<<
    this.spinSound = document.getElementById("spinSound");
    this.stopSpinSound = document.getElementById("stopSpinSound");
    this.winSound = document.getElementById("winSound");

    // >>> AMBIENTE <<<
    this.ambienteSound = document.getElementById("ambienteSound");
    if (this.ambienteSound) {
      this.ambienteSound.volume = 0.35;
      this.ambienteSound.loop = true;
      this.ambienteSound.play().catch(() => {});
    }

    this.betValue = 0.50;

    this.config = Object.assign(
      { betStep: 0.50, betMin: 0.50, betMax: 1000000 },
      config
    );

    this.currentSymbols = [
      ["1","2","3"],
      ["4","5","6"],
      ["7","8","9"],
      ["10","11","12"],
      ["13","15","15"]
    ];

    this.nextSymbols = JSON.parse(JSON.stringify(this.currentSymbols));
    this.container = domElement;

    this.reels = Array.from(
      this.container.getElementsByClassName("reel")
    ).map((reelContainer, idx) =>
      new Reel(reelContainer, idx, this.currentSymbols[idx])
    );

    this.spinButton = document.getElementById("spin");
    this.spinButton.addEventListener("click", () => this.spin());

    // ============================
    // AUTOPLAY
    // ============================
    this.autoPlayButton = document.getElementById("autoplayBtn");
    this.autoPlayBox = document.getElementById("autoplayBox");
    this.autoPlayBox.style.display = "none";
    this.autoPlaysLeft = 0;
    this.selectedAutoBtn = null;

    this.autoPlayButton.addEventListener("click", () => {
      this.autoPlayBox.style.display =
        this.autoPlayBox.style.display === "none" ? "block" : "none";
    });

    document.querySelectorAll(".autoOption").forEach(btn => {
      btn.addEventListener("click", () => {
        this.autoPlaysLeft = parseInt(btn.dataset.v);
        if (this.selectedAutoBtn) this.selectedAutoBtn.style.background = "#222";
        btn.style.background = "#555";
        this.selectedAutoBtn = btn;
      });
    });

    document.getElementById("startBtn").addEventListener("click", () => {
      if (this.autoPlaysLeft > 0) {
        this.autoPlayBox.style.display = "none";
        this.spin();
      }
    });

    window.slot = this;

    window.betMinus = () => {
      const step = parseFloat(this.config.betStep) || 0.5;
      this.betValue = Math.max(
        this.config.betMin,
        +(this.betValue - step).toFixed(2)
      );
      if (this.balance !== undefined && this.betValue > this.balance)
        this.betValue = this.balance;
      this.updateUI(0);
    };

    window.betPlus = () => {
      const step = parseFloat(this.config.betStep) || 0.5;
      this.betValue = Math.min(
        this.config.betMax,
        +(this.betValue + step).toFixed(2)
      );
      if (this.balance !== undefined && this.betValue > this.balance)
        this.betValue = this.balance;
      this.updateUI(0);
    };
  }

  // >>> CORRIGIDO: NÃO CHAMA /rodar NO LOAD <<<
  async init() {
    this.balance = parseFloat(
      this.balanceUI.textContent
        .replace("R$", "")
        .replace(",", ".")
    );
    this.updateUI(0);
  }

  updateUI(winAmount) {
    if (typeof this.balance === "undefined") return;

    if (this.balanceUI)
      this.balanceUI.textContent = "R$ " + this.balance.toFixed(2);

    if (this.betUI)
      this.betUI.textContent = "R$ " + this.betValue.toFixed(2);

    if (winAmount > 0 && this.winUI) {
      this.winUI.textContent = "R$ " + winAmount.toFixed(2);
      this.winUI.style.opacity = 0.5;
      setTimeout(() => (this.winUI.style.opacity = 0), 5000);
    }

    if (winAmount > 0 && this.espehoWinUI) {
      this.espehoWinUI.textContent = "R$ " + winAmount.toFixed(2);
      this.espehoWinUI.style.opacity = 0.5;
      setTimeout(() => (this.espehoWinUI.style.opacity = 0), 5000);
    }

    if (winAmount > 0 && this.winSound) {
      this.winSound.currentTime = 0;
      this.winSound.play().catch(()=>{});
    }

    if (this.balance <= 0) this.showDepositMessage();
  }

  showDepositMessage() {
    if (document.getElementById("deposit-message")) return;

    const msg = document.createElement("div");
    msg.id = "deposit-message";
    msg.style.position = "absolute";
    msg.style.top = "50%";
    msg.style.left = "50%";
    msg.style.transform = "translate(-50%, -50%)";
    msg.style.background = "#333";
    msg.style.padding = "20px";
    msg.style.color = "white";
    msg.style.border = "2px solid #000";
    msg.style.textAlign = "center";
    msg.style.width = "580px";
    msg.innerHTML =
      `<p>Saldo insuficiente!!</p>
       <button id="deposit-btn">Ir para Depósitos</button>`;

    document.body.appendChild(msg);

    document.getElementById("deposit-btn")
      .addEventListener("click", () => {
        window.location.href =
          `/metodos/pagamento/${window.USER_ID}`;
      });
  }

  async spin() {
    if (this.balance < this.betValue) return;

    this.spinButton.disabled = true;

    let backend = null;
    try {
      const resp = await fetch(`/rodar/${window.USER_ID}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bet: this.betValue })
      });
      backend = await resp.json();
      if (backend?.balance_user !== undefined)
        this.balance = parseFloat(backend.balance_user);
      if (backend?.grid)
        this.nextSymbols = backend.grid;
    } catch {}

    this.onSpinStart(this.nextSymbols);

    if (this.spinSound) {
      this.spinSound.currentTime = 0;
      this.spinSound.play().catch(()=>{});
    }

    await Promise.all(
      this.reels.map(reel => {
        reel.renderSymbols(this.nextSymbols[reel.idx]);
        return reel.spin();
      })
    );

    if (this.spinSound) {
      this.spinSound.pause();
      this.spinSound.currentTime = 0;
    }

    if (this.stopSpinSound) {
      this.stopSpinSound.currentTime = 0;
      this.stopSpinSound.play().catch(()=>{});
    }

    if (backend?.wins)
      backend.wins.forEach(win => this.highlightWin(win.positions));

    this.updateUI(backend?.win ? parseFloat(backend.win) : 0);

    this.onSpinEnd(backend?.wins || []);

    this.spinButton.disabled = false;

    if (this.autoPlaysLeft > 0) {
      this.autoPlaysLeft--;
      setTimeout(() => this.spin(), 200);
    }
  }

  highlightWin(positions) {
    const linesLayer =
      document.getElementById("linesLayer") || this.createLinesLayer();
    linesLayer.innerHTML = "";

    positions.forEach(([c, r]) => {
      const el = this.reels[c].symbolContainer.children[r];
      if (el) el.classList.add("win");
    });
  }

  onSpinStart(symbols) {}
  onSpinEnd(result) {}
}
