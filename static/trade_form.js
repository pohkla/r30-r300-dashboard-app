(() => {
  const fields = document.querySelectorAll('[data-datetime-field]');
  const form = document.querySelector('[data-trade-form]');
  if (!fields.length) return;

  const pad = (value) => String(value).padStart(2, '0');
  const THAI_MONTHS = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];
  const THAI_WEEKDAYS = ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'];

  const toDisplayDate = (isoDate) => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate || '');
    return match ? `${match[3]}/${match[2]}/${match[1]}` : '';
  };

  const parseDisplayDate = (value) => {
    const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec((value || '').trim());
    if (!match) return null;

    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);
    const date = new Date(year, month - 1, day);

    if (
      date.getFullYear() !== year ||
      date.getMonth() !== month - 1 ||
      date.getDate() !== day
    ) return null;

    return `${year}-${pad(month)}-${pad(day)}`;
  };

  const isoToDate = (isoDate) => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate || '');
    if (!match) return null;
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  };

  const dateToIso = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;

  const parseTime = (value) => {
    const match = /^(\d{2}):(\d{2})$/.exec((value || '').trim());
    if (!match) return null;
    const hour = Number(match[1]);
    const minute = Number(match[2]);
    if (hour > 23 || minute > 59) return null;
    return `${pad(hour)}:${pad(minute)}`;
  };

  const timeToMinutes = (value) => {
    const parsed = parseTime(value);
    if (!parsed) return Number.POSITIVE_INFINITY;
    const [hour, minute] = parsed.split(':').map(Number);
    return hour * 60 + minute;
  };

  const formatDateTyping = (value) => {
    const digits = value.replace(/\D/g, '').slice(0, 8);
    if (digits.length <= 2) return digits;
    if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
    return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
  };

  const formatTimeTyping = (value) => {
    const digits = value.replace(/\D/g, '').slice(0, 4);
    if (digits.length <= 2) return digits;
    return `${digits.slice(0, 2)}:${digits.slice(2)}`;
  };

  const localNowParts = () => {
    const now = new Date();
    return {
      isoDate: dateToIso(now),
      time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
    };
  };

  const closeAllCalendars = (except = null) => {
    document.querySelectorAll('.r300-calendar.is-open').forEach((calendar) => {
      if (calendar !== except) calendar.classList.remove('is-open');
    });
  };

  const closeAllTimePickers = (except = null) => {
    document.querySelectorAll('.r300-time-picker.is-open').forEach((picker) => {
      if (picker !== except) picker.classList.remove('is-open');
    });
  };

  const initField = (root) => {
    const hidden = root.querySelector('[data-datetime-value]');
    const dateText = root.querySelector('[data-date-text]');
    const timeText = root.querySelector('[data-time-text]');
    const calendarButton = root.querySelector('[data-open-calendar]');
    const nowButton = root.querySelector('[data-now]');
    const todayButton = root.querySelector('[data-today]');
    const clearButton = root.querySelector('[data-clear]');
    const dateControl = dateText.closest('.datetime-control');
    const timeControl = timeText.closest('.datetime-control');

    let viewDate = new Date();

    const calendar = document.createElement('div');
    calendar.className = 'r300-calendar';
    calendar.setAttribute('role', 'dialog');
    calendar.setAttribute('aria-label', 'เลือกวันที่');
    calendar.innerHTML = `
      <div class="r300-calendar-head">
        <button type="button" class="r300-calendar-nav" data-cal-prev aria-label="เดือนก่อนหน้า">‹</button>
        <strong data-cal-title></strong>
        <button type="button" class="r300-calendar-nav" data-cal-next aria-label="เดือนถัดไป">›</button>
      </div>
      <div class="r300-calendar-weekdays">
        ${THAI_WEEKDAYS.map((day) => `<span>${day}</span>`).join('')}
      </div>
      <div class="r300-calendar-days" data-cal-days></div>
      <div class="r300-calendar-footer">
        <button type="button" data-cal-today>วันนี้</button>
        <button type="button" data-cal-close>ปิด</button>
      </div>`;
    dateControl.appendChild(calendar);

    const title = calendar.querySelector('[data-cal-title]');
    const days = calendar.querySelector('[data-cal-days]');
    const prev = calendar.querySelector('[data-cal-prev]');
    const next = calendar.querySelector('[data-cal-next]');
    const calendarToday = calendar.querySelector('[data-cal-today]');
    const calendarClose = calendar.querySelector('[data-cal-close]');

    const timePicker = document.createElement('div');
    timePicker.className = 'r300-time-picker';
    timePicker.setAttribute('role', 'dialog');
    timePicker.setAttribute('aria-label', 'เลือกเวลาแบบ 24 ชั่วโมง');
    timePicker.innerHTML = `
      <div class="r300-time-head">
        <div>
          <strong data-time-title>เลือกเวลา</strong>
          <small>24 ชั่วโมง</small>
        </div>
        <button type="button" class="r300-time-close" data-time-close aria-label="ปิดตัวเลือกเวลา">×</button>
      </div>
      <div class="r300-time-list" data-time-list></div>`;
    timeControl.appendChild(timePicker);

    const timeTitle = timePicker.querySelector('[data-time-title]');
    const timeList = timePicker.querySelector('[data-time-list]');
    const timeClose = timePicker.querySelector('[data-time-close]');

    const splitValue = () => {
      const raw = (hidden.value || '').trim();
      const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(raw);
      if (!match) return { isoDate: '', time: '' };
      return { isoDate: match[1], time: match[2] };
    };

    const markValidity = (input, valid, message = '') => {
      input.classList.toggle('is-invalid', !valid);
      input.setAttribute('aria-invalid', valid ? 'false' : 'true');
      input.setCustomValidity(valid ? '' : message);
    };

    const sync = ({ validate = false } = {}) => {
      const dateRaw = dateText.value.trim();
      const timeRaw = timeText.value.trim();
      const isoDate = dateRaw ? parseDisplayDate(dateRaw) : null;
      const time = timeRaw ? parseTime(timeRaw) : null;

      const dateValid = !dateRaw || Boolean(isoDate);
      const timeValid = !timeRaw || Boolean(time);
      markValidity(dateText, dateValid, 'กรุณาระบุวันที่รูปแบบ dd/mm/yyyy เช่น 09/09/2026');
      markValidity(timeText, timeValid, 'กรุณาระบุเวลาแบบ 24 ชั่วโมง เช่น 22:47');

      if (!dateRaw && !timeRaw) {
        hidden.value = '';
      } else if (isoDate && time) {
        hidden.value = `${isoDate}T${time}`;
      } else {
        hidden.value = '';
      }

      if (validate && (!dateValid || !timeValid || Boolean(dateRaw) !== Boolean(timeRaw))) {
        if (Boolean(dateRaw) !== Boolean(timeRaw)) {
          if (!dateRaw) markValidity(dateText, false, 'กรุณาระบุวันที่ให้ครบคู่กับเวลา');
          if (!timeRaw) markValidity(timeText, false, 'กรุณาระบุเวลาให้ครบคู่กับวันที่');
        }
        return false;
      }
      return true;
    };

    const setParts = (isoDate, time) => {
      dateText.value = isoDate ? toDisplayDate(isoDate) : '';
      timeText.value = time || '';
      sync();
    };

    const renderCalendar = () => {
      const year = viewDate.getFullYear();
      const month = viewDate.getMonth();
      title.textContent = `${THAI_MONTHS[month]} ${year}`;
      days.innerHTML = '';

      const firstDay = new Date(year, month, 1).getDay();
      const lastDate = new Date(year, month + 1, 0).getDate();
      const selectedIso = parseDisplayDate(dateText.value);
      const todayIso = dateToIso(new Date());

      for (let i = 0; i < firstDay; i += 1) {
        const blank = document.createElement('span');
        blank.className = 'r300-calendar-blank';
        days.appendChild(blank);
      }

      for (let day = 1; day <= lastDate; day += 1) {
        const date = new Date(year, month, day);
        const iso = dateToIso(date);
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'r300-calendar-day';
        button.textContent = String(day);
        button.dataset.isoDate = iso;
        button.setAttribute('aria-label', `${day} ${THAI_MONTHS[month]} ${year}`);
        if (iso === todayIso) button.classList.add('is-today');
        if (iso === selectedIso) button.classList.add('is-selected');
        days.appendChild(button);
      }
    };

    const renderTimePicker = () => {
      const selected = parseTime(timeText.value);
      const options = [];
      for (let hour = 0; hour < 24; hour += 1) {
        options.push(`${pad(hour)}:00`, `${pad(hour)}:30`);
      }
      if (selected && !options.includes(selected)) options.push(selected);
      options.sort((a, b) => timeToMinutes(a) - timeToMinutes(b));

      timeTitle.textContent = selected || 'เลือกเวลา';
      timeList.innerHTML = options.map((value) => (
        `<button type="button" class="r300-time-option${value === selected ? ' is-selected' : ''}" data-time-option="${value}" aria-label="เลือกเวลา ${value}">${value}</button>`
      )).join('');
    };

    const openCalendar = () => {
      const selected = isoToDate(parseDisplayDate(dateText.value));
      viewDate = selected || new Date();
      viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
      renderCalendar();
      closeAllTimePickers();
      closeAllCalendars(calendar);
      calendar.classList.add('is-open');
    };

    const closeCalendar = () => calendar.classList.remove('is-open');

    const openTimePicker = () => {
      renderTimePicker();
      closeAllCalendars();
      closeAllTimePickers(timePicker);
      timePicker.classList.add('is-open');
      window.requestAnimationFrame(() => {
        const selectedButton = timePicker.querySelector('.r300-time-option.is-selected');
        if (selectedButton) {
          selectedButton.scrollIntoView({ block: 'center' });
        } else {
          const now = localNowParts().time;
          const nearestMinute = Number(now.slice(3, 5)) < 30 ? '00' : '30';
          const nearest = `${now.slice(0, 2)}:${nearestMinute}`;
          timePicker.querySelector(`[data-time-option="${nearest}"]`)?.scrollIntoView({ block: 'center' });
        }
      });
    };

    const closeTimePicker = () => timePicker.classList.remove('is-open');

    const initial = splitValue();
    setParts(initial.isoDate, initial.time);

    dateText.addEventListener('input', () => {
      dateText.value = formatDateTyping(dateText.value);
      sync();
    });
    dateText.addEventListener('focus', openCalendar);
    dateText.addEventListener('click', openCalendar);
    dateText.addEventListener('blur', () => {
      window.setTimeout(() => sync({ validate: Boolean(dateText.value || timeText.value) }), 0);
    });

    timeText.addEventListener('input', () => {
      timeText.value = formatTimeTyping(timeText.value);
      sync();
      if (timePicker.classList.contains('is-open')) renderTimePicker();
    });
    timeText.addEventListener('focus', openTimePicker);
    timeText.addEventListener('click', openTimePicker);
    timeText.addEventListener('blur', () => {
      window.setTimeout(() => sync({ validate: Boolean(dateText.value || timeText.value) }), 0);
    });

    calendarButton.addEventListener('click', (event) => {
      event.stopPropagation();
      if (calendar.classList.contains('is-open')) closeCalendar();
      else openCalendar();
    });

    prev.addEventListener('click', (event) => {
      event.stopPropagation();
      viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
      renderCalendar();
    });

    next.addEventListener('click', (event) => {
      event.stopPropagation();
      viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
      renderCalendar();
    });

    days.addEventListener('click', (event) => {
      const button = event.target.closest('[data-iso-date]');
      if (!button) return;
      event.stopPropagation();
      dateText.value = toDisplayDate(button.dataset.isoDate);
      sync();
      closeCalendar();
      timeText.focus();
    });

    calendarToday.addEventListener('click', (event) => {
      event.stopPropagation();
      const now = localNowParts();
      dateText.value = toDisplayDate(now.isoDate);
      sync();
      closeCalendar();
      timeText.focus();
    });

    calendarClose.addEventListener('click', (event) => {
      event.stopPropagation();
      closeCalendar();
    });

    calendar.addEventListener('click', (event) => event.stopPropagation());

    timeList.addEventListener('click', (event) => {
      const button = event.target.closest('[data-time-option]');
      if (!button) return;
      event.stopPropagation();
      timeText.value = button.dataset.timeOption;
      sync();
      closeTimePicker();
    });

    timeClose.addEventListener('click', (event) => {
      event.stopPropagation();
      closeTimePicker();
    });

    timePicker.addEventListener('click', (event) => event.stopPropagation());

    nowButton.addEventListener('click', () => {
      const now = localNowParts();
      setParts(now.isoDate, now.time);
      closeCalendar();
      closeTimePicker();
    });

    todayButton.addEventListener('click', () => {
      const now = localNowParts();
      const currentTime = parseTime(timeText.value) || now.time;
      setParts(now.isoDate, currentTime);
      closeCalendar();
      closeTimePicker();
    });

    clearButton.addEventListener('click', () => {
      setParts('', '');
      markValidity(dateText, true);
      markValidity(timeText, true);
      closeCalendar();
      closeTimePicker();
      dateText.focus();
    });

    return { root, sync, dateText, timeText };
  };

  const controllers = Array.from(fields, initField);

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.datetime-control')) {
      closeAllCalendars();
      closeAllTimePickers();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeAllCalendars();
      closeAllTimePickers();
    }
  });

  form?.addEventListener('submit', (event) => {
    let valid = true;
    let firstInvalid = null;

    controllers.forEach((controller) => {
      if (!controller.sync({ validate: true })) {
        valid = false;
        firstInvalid ||= controller.dateText.matches(':invalid') ? controller.dateText : controller.timeText;
      }
    });

    if (!valid) {
      event.preventDefault();
      firstInvalid?.focus();
      firstInvalid?.reportValidity();
    }
  });
})();