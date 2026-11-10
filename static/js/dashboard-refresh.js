const menuButton = document.querySelector('.sidebar-toggle');
if (menuButton) {
  menuButton.addEventListener('click', () => {
    const open = document.querySelector('.app-shell').classList.toggle('navigation-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      document.querySelector('.app-shell').classList.remove('navigation-open');
      menuButton.setAttribute('aria-expanded', 'false');
    }
  });
}
document.querySelectorAll('[data-calendar]').forEach(calendar => {
  const today = calendar.dataset.today;
  const selected = /^\d{4}-\d{2}-\d{2}$/.test(calendar.dataset.selected) ? calendar.dataset.selected : today;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(today)) return;
  let year = Number(selected.slice(0, 4)), month = Number(selected.slice(5, 7)) - 1;
  const nextButton = calendar.querySelector('[data-calendar-next]');
  const previousButton = calendar.querySelector('[data-calendar-prev]');
  function renderCalendar() {
    calendar.querySelector('[data-calendar-title]').textContent = `${year}년 ${month + 1}월`;
    nextButton.disabled = year > Number(today.slice(0, 4)) || (year === Number(today.slice(0, 4)) && month >= Number(today.slice(5, 7)) - 1);
    previousButton.disabled = year <= 1 && month === 0;
    const days = calendar.querySelector('[data-calendar-days]');
    days.replaceChildren();
    const first = new Date(0); first.setFullYear(year, month, 1); first.setHours(0, 0, 0, 0);
    const offset = (first.getDay() + 6) % 7;
    const end = new Date(first); end.setMonth(month + 1, 0);
    for (let i = 0; i < offset; i++) {
      const spacer = document.createElement('span'); spacer.className = 'calendar-spacer'; days.append(spacer);
    }
    for (let day = 1; day <= end.getDate(); day++) {
      const iso = `${String(year).padStart(4, '0')}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const button = document.createElement('button'); button.type = 'button'; button.textContent = day;
      button.setAttribute('aria-label', `${year}년 ${month + 1}월 ${day}일 기록 조회`);
      button.classList.toggle('is-selected', iso === selected); button.classList.toggle('is-today', iso === today);
      button.setAttribute('aria-pressed', String(iso === selected));
      if (iso === today) button.setAttribute('aria-current', 'date');
      button.disabled = iso > today;
      button.addEventListener('click', () => {
        const url = new URL(location.href); url.searchParams.set('start', iso); url.searchParams.set('end', iso); url.searchParams.delete('page'); location.assign(url.href);
      });
      days.append(button);
    }
  }
  previousButton.addEventListener('click', () => { if (--month < 0) { month = 11; year--; } renderCalendar(); });
  nextButton.addEventListener('click', () => { if (++month > 11) { month = 0; year++; } renderCalendar(); });
  renderCalendar();
});

function revealFilterAnchor() {
  if (location.hash === '#analysis-filters') {
    const filter = document.getElementById('analysis-filters');
    if (filter) filter.open = true;
  }
}
window.addEventListener('hashchange', revealFilterAnchor);
revealFilterAnchor();
const periodParams = new URL(location.href).searchParams;
const periodButtons = [...document.querySelectorAll('[data-period-start]')];
periodButtons.forEach((button, index) => {
  const active = periodParams.has('start')
    ? periodParams.get('start') === button.dataset.periodStart && periodParams.get('end') === button.dataset.periodEnd
    : index === periodButtons.length - 1;
  button.classList.toggle('active', active);
  button.setAttribute('aria-pressed', String(active));
});
