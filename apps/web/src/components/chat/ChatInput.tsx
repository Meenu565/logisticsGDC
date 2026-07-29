import { FormEvent, useMemo, useRef, useState } from "react";
import { FileSpreadsheet, Mic, RotateCcw, Send, Upload } from "lucide-react";
import { Button } from "../ui/button";

type ChatInputProps = {
  onSend: (message: string) => void;
  onImport: (file: File, mode: "append" | "replace") => void;
  onReset: () => void;
  disabled?: boolean;
};

export function ChatInput({ onSend, onImport, onReset, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [listening, setListening] = useState(false);
  const [importMode, setImportMode] = useState<"append" | "replace">("append");
  const fileRef = useRef<HTMLInputElement | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const speechSupported = useMemo(
    () => typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
    [],
  );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  };

  const openFilePicker = () => fileRef.current?.click();

  const toggleVoice = () => {
    if (!speechSupported) return;
    if (recognitionRef.current && listening) {
      recognitionRef.current.stop();
      return;
    }
    const Recognition = (window.SpeechRecognition ?? window.webkitSpeechRecognition)!;
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) setValue((current) => `${current} ${transcript}`.trim());
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  };

  return (
    <form onSubmit={submit} className="rounded-[28px] border border-white/10 bg-[#0b1220] p-2 shadow-soft">
      <input
        ref={fileRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onImport(file, importMode);
          event.currentTarget.value = "";
        }}
      />
      <div className="flex min-h-14 items-center gap-2">
        <select
          value={importMode}
          onChange={(event) => setImportMode(event.target.value === "replace" ? "replace" : "append")}
          className="h-10 rounded-xl border border-white/10 bg-white/[0.045] px-2 text-xs text-slate-200 outline-none"
          aria-label="Import mode"
        >
          <option value="append">Append</option>
          <option value="replace">Replace</option>
        </select>
        <Button type="button" variant="secondary" onClick={openFilePicker}>
          <Upload className="h-4 w-4" />
          Import Orders
        </Button>
        <Button type="button" variant="ghost" onClick={openFilePicker}>
          <FileSpreadsheet className="h-4 w-4" />
          Attach CSV/Excel
        </Button>
        <Button type="button" variant="ghost" onClick={onReset} disabled={disabled}>
          <RotateCcw className="h-4 w-4" />
          Reset
        </Button>
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Ask me anything about today's deliveries..."
          className="min-w-0 flex-1 bg-transparent px-3 text-[15px] text-white outline-none placeholder:text-slate-500"
        />
        <Button
          type="button"
          variant={listening ? "secondary" : "ghost"}
          size="icon"
          aria-label="Voice"
          onClick={toggleVoice}
          disabled={!speechSupported}
          title={speechSupported ? "Voice" : "Voice input is not available in this browser"}
        >
          <Mic className="h-4 w-4" />
        </Button>
        <Button type="submit" size="icon" disabled={disabled || !value.trim()} aria-label="Send">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}
