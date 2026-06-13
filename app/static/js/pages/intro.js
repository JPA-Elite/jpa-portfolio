// ---- CANVAS NEURAL NETWORK ANIMATION ----
const canvas = document.getElementById("brainCanvas");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();

let nodes = [];
const numNodes = window.innerWidth < 600 ? 75 : 150;

for (let i = 0; i < numNodes; i++) {
    nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 3 + 1.5,
        speedX: (Math.random() - 0.5) * 2,
        speedY: (Math.random() - 0.5) * 2,
        flicker: Math.random() < 0.15
    });
}

function drawConnections() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "limegreen";
    ctx.strokeStyle = "limegreen";
    ctx.lineWidth = 1.2;

    for (let i = 0; i < nodes.length; i++) {
        let nodeA = nodes[i];
        ctx.beginPath();
        ctx.arc(nodeA.x, nodeA.y, nodeA.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < nodes.length; j++) {
            let nodeB = nodes[j];
            let distance = Math.hypot(nodeA.x - nodeB.x, nodeA.y - nodeB.y);
            if (distance < 100) {
                ctx.globalAlpha = 1 - (distance / 100);
                ctx.beginPath();
                ctx.moveTo(nodeA.x, nodeA.y);
                ctx.lineTo(nodeB.x, nodeB.y);
                ctx.stroke();
            }
        }
    }
}

function updateNodes() {
    for (let node of nodes) {
        node.x += node.speedX;
        node.y += node.speedY;
        if (node.x < 0 || node.x > canvas.width) node.speedX *= -1;
        if (node.y < 0 || node.y > canvas.height) node.speedY *= -1;
        if (node.flicker && Math.random() < 0.1) {
            node.x += Math.random() * 6 - 3;
            node.y += Math.random() * 6 - 3;
        }
    }
}

function animateBrain() {
    drawConnections();
    updateNodes();
    requestAnimationFrame(animateBrain);
}

animateBrain();

// ---- GLITCH TYPEWRITER EFFECT ----
const text = "WELCOME TO MY PORTFOLIO";
let index = 0;
const speed = 80;
const typewriterElement = document.getElementById("typewriter");

function typeWriter() {
    typewriterElement.style.opacity = 1;
    if (index < text.length) {
        typewriterElement.innerHTML += text.charAt(index);
        index++;
        setTimeout(typeWriter, speed);
    } else {
        typewriterElement.style.borderRight = "none";
        setTimeout(() => { document.body.style.animation = "heartbeat 0.5s infinite alternate"; }, 2000);
        setTimeout(() => {
            document.body.style.animation = "none";
            document.body.style.backgroundColor = "white";
            document.body.style.color = "black";
        }, 3500);
        setTimeout(() => { window.location.href = "/profile"; }, 5000);
    }
}

setTimeout(typeWriter, 2500);