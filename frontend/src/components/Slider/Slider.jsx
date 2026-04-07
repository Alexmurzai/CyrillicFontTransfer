import './Slider.css';

export default function Slider({ label, value, min, max, step = 1, onChange, id }) {
  return (
    <div className="slider" id={id}>
      <div className="slider__header">
        <span className="slider__label">{label}</span>
        <span className="slider__value">{value}</span>
      </div>
      <input
        type="range"
        className="slider__input"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange?.(Number(e.target.value))}
      />
    </div>
  );
}
