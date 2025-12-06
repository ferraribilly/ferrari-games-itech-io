import Reel from "./Reel5x3.js";
import Symbol from "./Symbol5x3.js";

export default class Slot {
  constructor(domElement, config={}) {
    Symbol.preload();
    this.balanceUI = document.getElementById("balance");
    this.betUI = document.getElementById("betValue");
    this.winUI = document.getElementById("win");
    this.betValue = 0.50;

    this.config = Object.assign({
      betStep: 0.50,
      betMin: 0.50,
      betMax: 1000000
    }, config);

    this.currentSymbols = [
      ["avestruz","aguia","burro","borboleta","cachorro"],
      ["cabra","carneiro","camelo","cobra","coelho"],
      ["cavalo","elefante","galo","gato","jacare"],
      ["leao","macaco","porco","pavao","peru"],
      ["touro","tigre","urso","veado","vaca"],
    ];

    this.nextSymbols = JSON.parse(JSON.stringify(this.currentSymbols));
    this.container = domElement;

    this.reels = Array.from(this.container.getElementsByClassName("reel"))
      .map((reelContainer, idx) => new Reel(reelContainer, idx, this.currentSymbols[idx]));

    this.spinButton = document.getElementById("spin");
    this.spinButton.addEventListener("click", () => this.spin());
    this.autoPlayCheckbox = document.getElementById("autoplay");

    window.slot = this;

    window.betMinus = () => {
      const step = parseFloat(this.config.betStep)||0.5;
      const newBet = +(this.betValue-step).toFixed(2);
      this.betValue = Math.max(this.config.betMin,newBet);
      if(this.balance!==undefined && this.betValue>this.balance) this.betValue=this.balance;
      this.updateUI(0);
    };

    window.betPlus = () => {
      const step = parseFloat(this.config.betStep)||0.5;
      const newBet = +(this.betValue+step).toFixed(2);
      this.betValue = Math.min(this.config.betMax,newBet);
      if(this.balance!==undefined && this.betValue>this.balance) this.betValue=this.balance;
      this.updateUI(0);
    };
  }

  async init() {
    try {
      const resp = await fetch(`/rodar3x3/${window.USER_ID}`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({bet:0})
      });
      const result = await resp.json();
      if(result && typeof result.balance_user!=="undefined") {
        this.balance = parseFloat(result.balance_user);
      }
    } catch(err){}
    this.updateUI(0);
  }

  updateUI(winAmount) {
    if(typeof this.balance==="undefined") return;
    if(this.balanceUI) this.balanceUI.textContent = "R$ "+this.balance.toFixed(2);
    if(this.betUI) this.betUI.textContent = "R$ "+this.betValue.toFixed(2);
    if(winAmount>0 && this.winUI){
      this.winUI.textContent = "R$ "+winAmount.toFixed(2);
      this.winUI.style.opacity = 0.50;
      setTimeout(()=>{this.winUI.style.opacity=0;},5000);
    }
    if(this.balance<=0) this.showDepositMessage();
  }

  showDepositMessage() {
    if(document.getElementById("deposit-message")) return;
    const msg = document.createElement("div");
    msg.id="deposit-message";
    msg.style.position="absolute";
    msg.style.top="50%";
    msg.style.left="50%";
    msg.style.transform="translate(-50%,-50%)";
    msg.style.background="#333";
    msg.style.padding="20px";
    msg.style.color="white";
    msg.style.border="2px solid #000";
    msg.style.textAlign="center";
    msg.style.width="580px";
    msg.innerHTML=`<p>Saldo insuficiente!!</p><button id="deposit-btn">Ir para Depósitos</button>`;
    document.body.appendChild(msg);
    document.getElementById("deposit-btn").addEventListener("click",()=>{
      window.location.href=`/acesso/users/compras/${window.USER_ID}`;
    });
  }

  async spin() {
    if(this.balance<this.betValue) return;
    this.spinButton.disabled=true;
    let backend=null;
    try {
      const resp = await fetch(`/rodar3x3/${window.USER_ID}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({bet:this.betValue})
      });
      backend = await resp.json();
      if(backend && typeof backend.balance_user!=="undefined")
        this.balance=parseFloat(backend.balance_user);
      if(backend && backend.grid)
        this.nextSymbols=backend.grid;
    } catch(err){}
    this.onSpinStart(this.nextSymbols);
    await Promise.all(this.reels.map(reel=>{
      reel.renderSymbols(this.nextSymbols[reel.idx]);
      return reel.spin();
    }));
    if(backend && backend.wins)
      backend.wins.forEach(win=>this.highlightWin(win.positions));
    const totalWin = backend?.win ? parseFloat(backend.win) : 0;
    this.updateUI(totalWin);
    this.onSpinEnd(backend?.wins||[]);
    this.spinButton.disabled=false;
    if(this.autoPlayCheckbox && this.autoPlayCheckbox.checked)
      setTimeout(()=>this.spin(),200);
  }

  highlightWin(positions){
    const linesLayer=document.getElementById("linesLayer")||this.createLinesLayer();
    linesLayer.innerHTML="";
    positions.forEach(([c,r])=>{
      const el=this.reels[c].symbolContainer.children[r];
      if(el) el.classList.add("win");
    });
  }

  createLinesLayer(){
    const layer=document.createElement("div");
    layer.id="linesLayer";
    layer.style.position="absolute";
    layer.style.top="0";
    layer.style.left="0";
    layer.style.width="100%";
    layer.style.height="100%";
    layer.style.pointerEvents="none";
    layer.style.zIndex="9999";
    this.container.appendChild(layer);
    return layer;
  }

  onSpinStart(symbols){ this.config.onSpinStart?.(symbols); }
  onSpinEnd(result){ this.config.onSpinEnd?.(result); }
}
