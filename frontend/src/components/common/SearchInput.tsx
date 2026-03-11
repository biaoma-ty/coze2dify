import { useState, useEffect, useRef } from "react";
import { Search } from "lucide-react";
import { useTranslation } from "react-i18next";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounce?: number;
}

export default function SearchInput({
  value,
  onChange,
  placeholder,
  debounce = 300,
}: SearchInputProps) {
  const { t } = useTranslation();
  const [local, setLocal] = useState(value);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setLocal(value);
  }, [value]);

  const handleChange = (next: string) => {
    setLocal(next);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => onChange(next), debounce);
  };

  return (
    <div className="search-input">
      <Search size={16} className="search-input__icon" />
      <input
        className="input search-input__field"
        type="text"
        value={local}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder || t("common.search")}
      />
    </div>
  );
}
