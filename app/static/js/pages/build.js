import { BookingService } from "../services/BookingService.js";

const bookingService = new BookingService();

(function () {
    const form = document.getElementById('bookingForm');
    if (!form) return;

    const submitBtn = document.getElementById('submitBtn');
    const submitIcon = document.getElementById('submitIcon');
    const submitText = document.getElementById('submitText');
    const serviceInput = document.getElementById('serviceInput');
    const serviceCards = document.querySelectorAll('.service-card');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const messageInput = document.getElementById('message');
    const dateHidden = document.querySelector('.dtp-field[data-type="date"] .dtp-hidden');
    const timeHidden = document.querySelector('.dtp-field[data-type="time"] .dtp-hidden');
    const nameCount = document.getElementById('nameCount');
    const messageCount = document.getElementById('messageCount');
    const emailMsg = document.getElementById('emailMsg');
    const statusEl = document.getElementById('bookingStatus');

    const labels = {
        sending: form.dataset.sendingLabel || 'Sending...',
        submit: form.dataset.submitLabel || 'Submit Build',
        invalidEmail: form.dataset.invalidEmail || 'Invalid email format',
        retryIn: form.dataset.retryIn || 'Retry in',
        genericError: form.dataset.genericError || 'An error occurred. Please try again.',
        networkError: form.dataset.networkError || 'Network error. Please check your connection and try again.',
    };

    serviceCards.forEach(function (card) {
        card.addEventListener('click', function () {
            serviceCards.forEach(function (c) { c.classList.remove('selected'); });
            this.classList.add('selected');
            serviceInput.value = this.dataset.service;
            clearStatus();
        });
    });

    function validateEmail(val) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
    }

    function validateForm() {
        const nameVal = nameInput.value.trim();
        const emailVal = emailInput.value.trim();
        const dateVal = dateHidden ? dateHidden.value : '';
        const timeVal = timeHidden ? timeHidden.value : '';
        const msgVal = messageInput.value.trim();

        let valid = true;

        if (!nameVal || nameVal.length > 50) valid = false;
        if (!emailVal || !validateEmail(emailVal)) valid = false;
        if (!dateVal) valid = false;
        if (!timeVal) valid = false;
        if (!msgVal || msgVal.length > 500) valid = false;

        submitBtn.disabled = !valid;
    }

    function setStatus(message, type) {
        statusEl.textContent = message;
        statusEl.className = 'booking-status booking-status--' + type;
    }

    function clearStatus() {
        statusEl.textContent = '';
        statusEl.className = 'booking-status';
    }

    function setLoading(loading) {
        if (loading) {
            submitBtn.disabled = true;
            submitIcon.setAttribute('name', 'hourglass-outline');
            submitText.textContent = labels.sending;
        } else {
            submitIcon.setAttribute('name', 'paper-plane-outline');
            submitText.textContent = labels.submit;
            validateForm();
        }
    }

    nameInput.addEventListener('input', function () {
        const len = this.value.length;
        nameCount.textContent = len;
        if (len > 50) nameCount.style.color = '#e74c3c';
        else nameCount.style.color = '';
        clearStatus();
        validateForm();
    });

    emailInput.addEventListener('input', function () {
        const val = this.value.trim();
        if (val && !validateEmail(val)) {
            emailMsg.textContent = labels.invalidEmail;
            emailMsg.style.color = '#e74c3c';
        } else {
            emailMsg.textContent = '';
        }
        clearStatus();
        validateForm();
    });

    messageInput.addEventListener('input', function () {
        const len = this.value.length;
        messageCount.textContent = len;
        if (len > 500) messageCount.style.color = '#e74c3c';
        else messageCount.style.color = '';
        clearStatus();
        validateForm();
    });

    if (dateHidden) dateHidden.addEventListener('change', function () { clearStatus(); validateForm(); });
    if (timeHidden) timeHidden.addEventListener('change', function () { clearStatus(); validateForm(); });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (submitBtn.disabled) return;
        clearStatus();
        setLoading(true);

        const captchaInput = document.querySelector('[name="h-captcha-response"]');
        const captchaToken = captchaInput ? captchaInput.value : '';

        bookingService.send({
            name: nameInput.value.trim(),
            email: emailInput.value.trim(),
            preferred_date: dateHidden ? dateHidden.value : '',
            preferred_time: timeHidden ? timeHidden.value : '',
            message: messageInput.value.trim(),
            service: serviceInput.value,
            hcaptcha_token: captchaToken,
        })
        .then(function (result) {
            const data = result.data || {};
            if (data.ok) {
                setStatus(data.message, 'success');
                form.reset();
                serviceInput.value = '';
                serviceCards.forEach(function (c) { c.classList.remove('selected'); });
                if (typeof hcaptcha !== 'undefined') hcaptcha.reset();
                if (dateHidden) dateHidden.value = '';
                if (timeHidden) timeHidden.value = '';
                nameCount.textContent = '0';
                messageCount.textContent = '0';
                emailMsg.textContent = '';
                validateForm();
            } else if (result.status === 429) {
                let retryAfter = data.retry_after_seconds || 3600;
                setStatus(data.message, 'error');
                submitBtn.disabled = true;
                const countdownEl = document.createElement('div');
                countdownEl.className = 'booking-retry-countdown';
                statusEl.appendChild(countdownEl);
                const interval = setInterval(function () {
                    if (retryAfter <= 0) {
                        clearInterval(interval);
                        countdownEl.remove();
                        validateForm();
                        return;
                    }
                    const mins = Math.floor(retryAfter / 60);
                    const secs = retryAfter % 60;
                    countdownEl.textContent = labels.retryIn + ' ' + mins + 'm ' + secs + 's';
                    retryAfter--;
                }, 1000);
            } else {
                setStatus(data.message || labels.genericError, 'error');
            }
        })
        .catch(function () {
            setStatus(labels.networkError, 'error');
        })
        .finally(function () {
            setLoading(false);
        });
    });

    validateForm();
})();
