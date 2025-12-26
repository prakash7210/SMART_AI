 function ToggleSwitch({ isOn, setIsOn }) {
  return (
    <div className="toggle">
      <span>Text</span>
      <label className="switch">
        <input type="checkbox" checked={isOn} onChange={() => setIsOn(!isOn)} />
        <span className="slider"></span>
      </label>
      <span>Image</span>
    </div>
  );
}
export default ToggleSwitch;
