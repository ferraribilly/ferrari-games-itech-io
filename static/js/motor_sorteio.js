const totalBolas = 90;
const container = document.getElementById('globo');
let sorteados = [];
const bolinhas = [];

function criarBolinhas(){
  container.innerHTML = '';
  bolinhas.length = 0;
  const cw = container.clientWidth;
  const ch = container.clientHeight;
  const centerX = cw/2;
  const centerY = ch/2;
  const radius = Math.min(cw,ch)/2 - 25;

  for(let i=1;i<=totalBolas;i++){
    const bola = document.createElement('div');
    bola.className = 'bola';
    bola.textContent = i;
    container.appendChild(bola);

    const angle = Math.random() * 2 * Math.PI;
    const r = Math.sqrt(Math.random()) * radius;
    const x = centerX + r*Math.cos(angle) - 25;
    const y = centerY + r*Math.sin(angle) - 25;
    const vx = (Math.random()-0.5)*4;
    const vy = (Math.random()-0.5)*4;
    bolinhas.push({el:bola, x:x, y:y, vx:vx, vy:vy});
    bola.style.left = x+'px';
    bola.style.top = y+'px';
  }
}

let animando = false;
function animar(){
  const cw = container.clientWidth;
  const ch = container.clientHeight;
  const centerX = cw/2;
  const centerY = ch/2;
  const radius = Math.min(cw,ch)/2 - 25;

  bolinhas.forEach(b=>{
    b.x += b.vx;
    b.y += b.vy;
    const dx = (b.x+25)-centerX;
    const dy = (b.y+25)-centerY;
    const dist = Math.sqrt(dx*dx+dy*dy);
    if(dist>radius){
      const angle = Math.atan2(dy,dx);
      const pushX = centerX+radius*Math.cos(angle)-25;
      const pushY = centerY+radius*Math.sin(angle)-25;
      b.x = pushX; b.y = pushY;
      b.vx*=-0.8; b.vy*=-0.8;
    }
    b.vx = Math.max(Math.min(b.vx,6),-6);
    b.vy = Math.max(Math.min(b.vy,6),-6);
    b.el.style.left = b.x+'px';
    b.el.style.top = b.y+'px';
  });
  if(animando) requestAnimationFrame(animar);
}

function atualizarUltimos(){
  const ultimos = sorteados.slice(-6);
  const div = document.getElementById('ultimos_numeros');
  div.innerHTML = '';
  ultimos.forEach(n=>{
    const bola = document.createElement('div');
    bola.className = 'bola_ultima';
    bola.textContent = n;
    div.appendChild(bola);
  });
}

function sortearNumero(){
  let numero;
  do{
    numero = Math.floor(Math.random()*totalBolas)+1;
  }while(sorteados.includes(numero));
  sorteados.push(numero);
  bolinhas[numero-1].el.classList.add('sorteada');
  const td = document.querySelectorAll('.bolinha')[numero-1];
  td.classList.add('sorteada');
  atualizarUltimos();
  const msg = new SpeechSynthesisUtterance();
  msg.text = "Número sorteado: "+numero;
  msg.lang = "pt-BR"; msg.rate=1.3; msg.pitch=0.5;
  window.speechSynthesis.speak(msg);
}

const menuBtn = document.getElementById('menuBtn');
const menuLista = document.getElementById('menuLista');
menuBtn.addEventListener('click', ()=>{
  menuLista.style.display = menuLista.style.display === 'block' ? 'none' : 'block';
});

document.getElementById('girar').addEventListener('click', ()=>{
  animando = true;
  animar();
  sortearNumero();
});

window.addEventListener('resize', ()=>{ criarBolinhas(); });
criarBolinhas();

/* ===== Modal Comprar Ticket ===== */
const comprarTicketBtn = document.getElementById('comprarTicket');
const ticketModal = document.getElementById('ticketModal');
const ticketBolasDiv = document.getElementById('ticketBolas');
const comprarBtn = document.getElementById('comprarBtn');

let ticketNumeros = [null,null,null,null,null,null];

function criarTicketBolas(){
  ticketBolasDiv.innerHTML = '';
  for(let i=0;i<6;i++){
    const bola = document.createElement('div');
    bola.className = 'ticketBola';
    bola.dataset.index = i;
    bola.addEventListener('click', ()=>{
      const n = prompt("Digite o número da bola "+(i+1));
      if(n && !isNaN(n) && n>0 && n<=90){
        bola.textContent = n;
        bola.classList.add('filled');
        ticketNumeros[i] = n;
      }
    });
    ticketBolasDiv.appendChild(bola);
  }
}

comprarTicketBtn.addEventListener('click', ()=>{
  ticketModal.style.display = 'flex';
  criarTicketBolas();
});

comprarBtn.addEventListener('click', ()=>{
  const nome = document.getElementById('nome').value;
  const cpf = document.getElementById('cpf').value;
  const data = document.getElementById('data').value;
  const email = document.getElementById('email').value;
  if(!nome || !cpf || !data || !email || ticketNumeros.includes(null)){
    alert("Preencha todos os campos e números!");
    return;
  }
  const resumo = `Nome: ${nome}\nCPF: ${cpf}\nData Nascimento: ${data}\nEmail: ${email}\nNúmeros: ${ticketNumeros.join(', ')}\nValor: R$5,00`;
  if(confirm(resumo)){
    alert("Compra Confirmada!");
    ticketModal.style.display='none';
    ticketNumeros = [null,null,null,null,null,null];
    document.getElementById('nome').value='';
    document.getElementById('cpf').value='';
    document.getElementById('data').value='';
    document.getElementById('email').value='';
  }
});

function girarGlobo() {
  const globo = document.querySelector('#globo'); // precisa existir no HTML
  if (!globo) return;
  // aplica uma classe que faz uma animação de giro rápido (defina no CSS)
  globo.classList.add('girando-rapido');
  // remove a classe após 6s (quando o globo "para")
  setTimeout(() => {
    globo.classList.remove('girando-rapido');
  }, 6000);
}




ticketModal.addEventListener('click', (e)=>{
  if(e.target===ticketModal) ticketModal.style.display='none';
});
