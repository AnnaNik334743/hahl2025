CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    is_fixed_date BOOLEAN DEFAULT true,
    is_day_off BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO holidays (name, description, month, day, is_fixed_date, is_day_off) VALUES
('New Year', 'Новый год', 1, 1, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 2, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 3, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 4, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 5, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 6, true, true),
('Christmas', 'Рождество Христово', 1, 7, true, true),
('New Year Holiday', 'Праздничный день после Нового года', 1, 8, true, true),
('Defender of the Fatherland Day', 'День защитника Отечества', 2, 23, true, true),
('International Women''s Day', 'Международный женский день', 3, 8, true, true),
('Spring and Labor Day', 'Праздник Весны и Труда', 5, 1, true, true),
('Victory Day', 'День Победы', 5, 9, true, true),
('Russia Day', 'День России', 6, 12, true, true),
('Unity Day', 'День народного единства', 11, 4, true, true),
('Tatiana Day', 'День российского студенчества (Татьянин день)', 1, 25, true, false),
('Cosmonautics Day', 'День космонавтики', 4, 12, true, false),
('Knowledge Day', 'День знаний', 9, 1, true, false),
('Programmer''s Day', 'День программиста', 9, 13, true, false),
('Teacher''s Day', 'День учителя', 10, 5, true, false),
('Police Day', 'День сотрудника органов внутренних дел', 11, 10, true, false),
('Constitution Day', 'День Конституции Российской Федерации', 12, 12, true, false);

CREATE INDEX idx_holidays_month ON holidays(month);
CREATE INDEX idx_holidays_month_day ON holidays(month, day);

CREATE OR REPLACE FUNCTION get_holidays_by_month(month_num INTEGER)
RETURNS TABLE (
    holiday_id INTEGER,
    holiday_name VARCHAR(255),
    holiday_description TEXT,
    holiday_month INTEGER,
    holiday_day INTEGER,
    is_day_off BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.name,
        h.description,
        h.month,
        h.day,
        h.is_day_off
    FROM holidays h
    WHERE h.month = month_num
    ORDER BY h.day;
END;
$$ LANGUAGE plpgsql;