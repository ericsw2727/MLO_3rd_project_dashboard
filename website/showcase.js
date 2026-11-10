// NODEVERSE - Interactive Showcase, 3D Tilt & Robot Companion

document.addEventListener('DOMContentLoaded', () => {
  // 1. Interactive Stage Filtering
  const filterBtns = document.querySelectorAll('.stage-filter-btn');
  const stageCards = document.querySelectorAll('.stage-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');
      stageCards.forEach(card => {
        const cat = card.getAttribute('data-category');
        if (filter === 'all' || cat === filter) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // 2. 3D Card Tilt & Holographic Glare
  stageCards.forEach(card => {
    // Add glare element if missing
    if (!card.querySelector('.stage-card-glare')) {
      const glare = document.createElement('div');
      glare.className = 'stage-card-glare';
      card.appendChild(glare);
    }

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      // Calculate tilt angles (limit between -9 and 9 deg)
      const rotateX = ((y - centerY) / centerY) * -9;
      const rotateY = ((x - centerX) / centerX) * 9;

      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-8px) scale(1.02)`;

      const glare = card.querySelector('.stage-card-glare');
      if (glare) {
        glare.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(255,255,255,0.45) 0%, rgba(255,255,255,0) 65%)`;
      }
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px) scale(1)';
    });
  });

  // 3. Floating Robot Companion Interactions
  const robotAvatarBtn = document.getElementById('robot-avatar-btn');
  const robotBubble = document.getElementById('robot-bubble');
  const bubbleText = document.getElementById('bubble-text');
  const bubbleClose = document.getElementById('bubble-close');

  if (robotAvatarBtn) {
    // Bounce animation on click
    robotAvatarBtn.addEventListener('click', () => {
      robotAvatarBtn.classList.remove('robot-clicked');
      void robotAvatarBtn.offsetWidth; // trigger reflow
      robotAvatarBtn.classList.add('robot-clicked');
    });

    // Close button for bubble
    if (bubbleClose && robotBubble) {
      bubbleClose.addEventListener('click', (e) => {
        e.stopPropagation();
        robotBubble.style.opacity = '0';
        robotBubble.style.transform = 'scale(0.8)';
        setTimeout(() => {
          robotBubble.style.display = 'none';
        }, 200);
      });
    }
  }
});
