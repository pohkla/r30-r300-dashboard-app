(() => {
  const fields = document.querySelectorAll('[data-datetime-field]');
  const form = document.querySelector('[data-trade-form]');
  if (!fields.length) return;

  const pad = (value) => String(value).padStart(2, '0');

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

  const parseTime = (value) => {
    const match = /^(\d{2}):(\d{2})$/.exec((value || '').trim());
    if (!match) return null;
    const hour = Number(match[1]);
    const minute = Number(match[2]);
    if (hour > 23 || minute > 59) return null;
    return `${pad(hour)}:${pad(minute)}`;
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
      isoDate: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
    };
  };

  const initField = (root) => {
    const hidden = root.querySelector('[data-datetime-value]');
    const dateText = root.querySelector('[data-date-text]');
    const timeText = root.querySelector('[data-time-text]');
    const nativeDate = root.querySelector('[data-native-date]');
    const calendarButton = root.querySelector('[data-open-calendar]');
    const nowButton = root.querySelector('[data-now]');
    const todayButton = root.querySelector('[data-today]');
    const clearButton = root.querySelector('[data-clear]');

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

      nativeDate.value = isoDate || '';

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
      nativeDate.value = isoDate || '';
      sync();
    };

    const initial = splitValue();
    setParts(initial.isoDate, initial.time);

    dateText.addEventListener('input', () => {
      dateText.value = formatDateTyping(dateText.value);
      sync();
    });
    dateText.addEventListener('blur', () => sync({ validate: Boolean(dateText.value || timeText.value) }));

    timeText.addEventListener('input', () => {
      timeText.value = formatTimeTyping(timeText.value);
      sync();
    });
    timeText.addEventListener('blur', () => sync({ validate: Boolean(dateText.value || timeText.value) }));

    nativeDate.addEventListener('change', () => {
      if (nativeDate.value) dateText.value = toDisplayDate(nativeDate.value);
      sync();
      timeText.focus();
    });

    calendarButton.addEventListener('click', () => {
      const current = parseDisplayDate(dateText.value);
      if (current) nativeDate.value = current;
      if (typeof nativeDate.showPicker === 'function') {
        nativeDate.showPicker();
      } else {
        nativeDate.focus();
        nativeDate.click();
      }
    });

    nowButton.addEventListener('click', () => {
      const now = localNowParts();
      setParts(now.isoDate, now.time);
    });

    todayButton.addEventListener('click', () => {
      const now = localNowParts();
      const currentTime = parseTime(timeText.value) || now.time;
      setParts(now.isoDate, currentTime);
    });

    clearButton.addEventListener('click', () => {
      setParts('', '');
      markValidity(dateText, true);
      markValidity(timeText, true);
      dateText.focus();
    });

    return { root, sync, dateText, timeText };
  };

  const controllers = Array.from(fields, initField);

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