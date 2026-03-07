(() => {
    const pickers = Array.from(document.querySelectorAll("[data-date-picker]"));
    if (!pickers.length) return;

    const pad = (value) => String(value).padStart(2, "0");

    const parseDate = (value) => {
        if (!value) return null;
        const match = String(value).trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!match) return null;
        const year = Number(match[1]);
        const month = Number(match[2]) - 1;
        const day = Number(match[3]);
        const date = new Date(year, month, day);
        if (Number.isNaN(date.getTime())) return null;
        if (date.getFullYear() !== year || date.getMonth() !== month || date.getDate() !== day) return null;
        return date;
    };

    const formatDate = (date) => {
        if (!date) return "";
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
    };

    const buildPicker = (picker) => {
        const displayInput = picker.querySelector(".server-date-display");
        const valueInput = picker.querySelector(".server-date-value");
        const panel = picker.querySelector(".server-date-panel");
        const grid = picker.querySelector(".server-date-grid");
        const monthLabel = picker.querySelector(".server-date-month");
        const navButtons = picker.querySelectorAll(".server-date-nav");

        if (!displayInput || !valueInput || !panel || !grid || !monthLabel) return;

        let selectedDate = parseDate(valueInput.value) || parseDate(displayInput.value);
        let viewDate = selectedDate ? new Date(selectedDate) : new Date();

        const closePanel = () => {
            panel.classList.remove("is-open");
            panel.setAttribute("aria-hidden", "true");
        };

        const openPanel = () => {
            panel.classList.add("is-open");
            panel.setAttribute("aria-hidden", "false");
            renderCalendar();
        };

        const updateInputs = (date) => {
            selectedDate = date;
            const formatted = formatDate(date);
            displayInput.value = formatted;
            valueInput.value = formatted;
        };

        const renderCalendar = () => {
            const year = viewDate.getFullYear();
            const month = viewDate.getMonth();
            const firstDay = new Date(year, month, 1);
            const startDay = firstDay.getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();

            monthLabel.textContent = firstDay.toLocaleString(undefined, { month: "long", year: "numeric" });
            grid.innerHTML = "";

            for (let i = 0; i < startDay; i += 1) {
                const spacer = document.createElement("span");
                spacer.className = "server-date-day is-empty";
                grid.appendChild(spacer);
            }

            for (let day = 1; day <= daysInMonth; day += 1) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "server-date-day";
                button.textContent = String(day);
                const current = new Date(year, month, day);
                if (selectedDate && formatDate(current) === formatDate(selectedDate)) {
                    button.classList.add("is-selected");
                }
                button.addEventListener("click", () => {
                    updateInputs(current);
                    closePanel();
                });
                grid.appendChild(button);
            }
        };

        navButtons.forEach((btn) => {
            btn.addEventListener("click", (event) => {
                event.preventDefault();
                const action = btn.getAttribute("data-action");
                const delta = action === "prev" ? -1 : 1;
                viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + delta, 1);
                renderCalendar();
            });
        });

        displayInput.addEventListener("focus", openPanel);
        displayInput.addEventListener("click", openPanel);

        displayInput.addEventListener("blur", () => {
            const parsed = parseDate(displayInput.value);
            if (parsed) {
                updateInputs(parsed);
                viewDate = new Date(parsed);
            } else if (displayInput.value.trim() === "") {
                updateInputs(null);
            } else {
                displayInput.value = valueInput.value;
            }
        });

        document.addEventListener("click", (event) => {
            if (!picker.contains(event.target)) {
                closePanel();
            }
        });

        updateInputs(selectedDate);
    };

    pickers.forEach(buildPicker);
})();
