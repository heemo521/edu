import { useState } from 'react';

export default function Rating({ onRate }) {
  const [value, setValue] = useState(0);
  const handleClick = (v) => {
    setValue(v);
    onRate(v);
  };
  return (
    <span>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          onClick={() => handleClick(n)}
          style={{ cursor: 'pointer', color: n <= value ? '#ffc107' : '#e4e5e9' }}
        >
          ★
        </span>
      ))}
    </span>
  );
}
