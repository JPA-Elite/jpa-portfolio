(function () {
  const MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  function initPicker(container) {
    const type = container.dataset.type;
    const displayInput = container.querySelector('.dtp-input');
    const hiddenInput = container.querySelector('.dtp-hidden');
    const dropdown = container.querySelector('.dtp-dropdown');
    const icon = container.querySelector('.dtp-icon');

    function open() {
      dropdown.classList.add('open');
    }

    function close() {
      dropdown.classList.remove('open');
    }

    function isOpen() {
      return dropdown.classList.contains('open');
    }

    displayInput.addEventListener('click', function (e) {
      e.stopPropagation();
      if (isOpen()) { close(); return; }
      closeAllPickers();
      if (type === 'date') renderCalendar(dropdown, displayInput, hiddenInput);
      else if (type === 'time') renderTimeGrid(dropdown, displayInput, hiddenInput);
      open();
    });

    icon.addEventListener('click', function (e) {
      e.stopPropagation();
      displayInput.click();
    });

    document.addEventListener('click', function (e) {
      if (!container.contains(e.target)) close();
    });
  }

  function closeAllPickers() {
    document.querySelectorAll('.dtp-dropdown.open').forEach(function (d) {
      d.classList.remove('open');
    });
  }

  /* ---- Date Calendar ---- */
  function renderCalendar(dropdown, displayInput, hiddenInput) {
    var now = new Date();
    var todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var selectedDate = hiddenInput.value ? new Date(hiddenInput.value + 'T12:00:00') : null;
    var viewMonth = selectedDate ? selectedDate.getFullYear() + '-' + String(selectedDate.getMonth() + 1).padStart(2, '0') : now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');

    dropdown.innerHTML = '';

    var header = document.createElement('div');
    header.className = 'dtp-calendar-header';

    var monthLabel = document.createElement('span');
    monthLabel.className = 'dtp-calendar-month';

    var nav = document.createElement('div');
    nav.className = 'dtp-calendar-nav';

    var prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'dtp-nav-btn';
    prevBtn.innerHTML = '<ion-icon name="chevron-back-outline"></ion-icon>';
    nav.appendChild(prevBtn);

    var nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'dtp-nav-btn';
    nextBtn.innerHTML = '<ion-icon name="chevron-forward-outline"></ion-icon>';
    nav.appendChild(nextBtn);

    header.appendChild(monthLabel);
    header.appendChild(nav);
    dropdown.appendChild(header);

    var weekdaysRow = document.createElement('div');
    weekdaysRow.className = 'dtp-calendar-weekdays';
    WEEKDAYS.forEach(function (d) {
      var el = document.createElement('span');
      el.className = 'dtp-weekday';
      el.textContent = d;
      weekdaysRow.appendChild(el);
    });
    dropdown.appendChild(weekdaysRow);

    var daysGrid = document.createElement('div');
    daysGrid.className = 'dtp-calendar-days';
    dropdown.appendChild(daysGrid);

    function buildCalendar(viewVal) {
      var parts = viewVal.split('-');
      var year = parseInt(parts[0], 10);
      var month = parseInt(parts[1], 10) - 1;

      monthLabel.textContent = MONTHS[month] + ' ' + year;

      var firstDay = new Date(year, month, 1).getDay();
      var daysInMonth = new Date(year, month + 1, 0).getDate();
      var daysInPrev = new Date(year, month, 0).getDate();

      var todayStr = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
      var currentViewMonth = new Date(year, month, 1);
      var isPastView = currentViewMonth < new Date(todayStart.getFullYear(), todayStart.getMonth(), 1);

      prevBtn.disabled = isPastView;
      if (isPastView) prevBtn.style.opacity = '0.3';
      else prevBtn.style.opacity = '';

      daysGrid.innerHTML = '';

      for (var i = firstDay - 1; i >= 0; i--) {
        var el = document.createElement('button');
        el.type = 'button';
        el.className = 'dtp-day other-month';
        el.textContent = daysInPrev - i;
        el.disabled = true;
        daysGrid.appendChild(el);
      }

      for (var d = 1; d <= daysInMonth; d++) {
        var dateObj = new Date(year, month, d);
        var dateStr = year + '-' + String(month + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        var el = document.createElement('button');
        el.type = 'button';
        el.className = 'dtp-day';
        el.textContent = d;
        el.dataset.date = dateStr;

        if (dateStr === todayStr) el.classList.add('today');
        if (selectedDate && dateStr === hiddenInput.value) el.classList.add('selected');

        if (dateObj < todayStart) {
          el.classList.add('past');
          el.disabled = true;
        } else {
          el.addEventListener('click', function () {
            var val = this.dataset.date;
            hiddenInput.value = val;
            var d = new Date(val + 'T12:00:00');
            displayInput.value = formatDate(d);
            hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            closeAllPickers();
          });
        }

        daysGrid.appendChild(el);
      }

      var totalCells = firstDay + daysInMonth;
      var remaining = (7 - (totalCells % 7)) % 7;
      for (var i = 1; i <= remaining; i++) {
        var el = document.createElement('button');
        el.type = 'button';
        el.className = 'dtp-day other-month';
        el.textContent = i;
        el.disabled = true;
        daysGrid.appendChild(el);
      }
    }

    buildCalendar(viewMonth);

    prevBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (this.disabled) return;
      var parts = viewMonth.split('-');
      var y = parseInt(parts[0], 10);
      var m = parseInt(parts[1], 10) - 2;
      if (m < 0) { m = 11; y--; }
      viewMonth = y + '-' + String(m + 1).padStart(2, '0');
      buildCalendar(viewMonth);
    });

    nextBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var parts = viewMonth.split('-');
      var y = parseInt(parts[0], 10);
      var m = parseInt(parts[1], 10) + 1;
      if (m > 12) { m = 1; y++; }
      viewMonth = y + '-' + String(m).padStart(2, '0');
      buildCalendar(viewMonth);
    });
  }

  /* ---- Time Grid ---- */
  function renderTimeGrid(dropdown, displayInput, hiddenInput) {
    var selected = hiddenInput.value;
    var now = new Date();
    var dateField = document.querySelector('.dtp-field[data-type="date"]');
    var dateHidden = dateField ? dateField.querySelector('.dtp-hidden') : null;
    var selectedDate = dateHidden && dateHidden.value ? new Date(dateHidden.value + 'T12:00:00') : null;

    var isToday = selectedDate &&
      selectedDate.getFullYear() === now.getFullYear() &&
      selectedDate.getMonth() === now.getMonth() &&
      selectedDate.getDate() === now.getDate();

    var currentMinutes = now.getHours() * 60 + now.getMinutes();

    dropdown.innerHTML = '';

    var grid = document.createElement('div');
    grid.className = 'dtp-time-grid';

    var times = [];
    for (var h = 8; h <= 23; h++) {
      for (var m = 0; m < 60; m += 30) {
        var hour = h;
        var min = m;
        var ampm = hour >= 12 ? 'PM' : 'AM';
        var hour12 = hour % 12 || 12;
        var label = hour12 + ':' + String(min).padStart(2, '0') + ' ' + ampm;
        var val = String(hour).padStart(2, '0') + ':' + String(min).padStart(2, '0');
        var slotMinutes = hour * 60 + min;
        var past = isToday && slotMinutes < currentMinutes;
        times.push({ label: label, value: val, past: past });
      }
    }
    times.push({ label: '12:00 AM', value: '00:00', past: isToday && 0 < currentMinutes });

    times.forEach(function (t) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'dtp-time-slot';
      btn.textContent = t.label;
      btn.dataset.value = t.value;

      if (t.past) btn.classList.add('past');
      if (selected === t.value && !t.past) btn.classList.add('selected');

      if (!t.past) {
        btn.addEventListener('click', function () {
          var val = this.dataset.value;
          hiddenInput.value = val;
          displayInput.value = this.textContent;
          hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
          closeAllPickers();
        });
      }

      grid.appendChild(btn);
    });

    dropdown.appendChild(grid);

    if (!isToday && selected) {
      var selectedEl = grid.querySelector('.dtp-time-slot.selected');
      if (selectedEl) selectedEl.scrollIntoView({ block: 'center' });
    }
  }

  function formatDate(d) {
    var month = MONTHS[d.getMonth()];
    var day = d.getDate();
    var year = d.getFullYear();
    return month + ' ' + day + ', ' + year;
  }

  /* Init all pickers on page */
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dtp-field[data-type]').forEach(initPicker);
  });
})();
