import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { FileSpreadsheet, Mic, RotateCcw, Send, Square, Upload } from "lucide-react";
import { Button } from "../ui/button";
import { transcribeAudioBlob } from "../../services/dispatchApi";

type ChatInputProps = {
  onSend: (message: string) => void;
  onImport: (file: File, mode: "append" | "replace") => void;
  onReset: () => void;
  disabled?: boolean;
};

export function ChatInput({ onSend, onImport, onReset, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [importMode, setImportMode] = useState<"append" | "replace">("append");

  const fileRef = useRef<HTMLInputElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const speechSupported = useMemo(
    () => typeof window !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia),
    [],
  );

  useEffect(() => {
    if (recording) {
      setRecordSeconds(0);
      timerRef.current = window.setInterval(() => {
        setRecordSeconds((sec) => sec + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [recording]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim() || disabled || transcribing) return;
    onSend(value.trim());
    setValue("");
  };

  const openFilePicker = () => fileRef.current?.click();

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        if (audioBlob.size > 0) {
          await handleTranscribe(audioBlob);
        }
      };

      mediaRecorder.start(250);
      setRecording(true);
    } catch (err) {
      console.warn("Could not access microphone:", err);
      fallbackWebSpeech();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  };

  const toggleRecording = () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleTranscribe = async (audioBlob: Blob) => {
    try {
      setTranscribing(true);
      const text = await transcribeAudioBlob(audioBlob);
      if (text && text.trim()) {
        setValue((prev) => (prev ? `${prev} ${text.trim()}` : text.trim()));
      }
    } catch (err) {
      console.error("Deepgram transcription failed:", err);
    } finally {
      setTranscribing(false);
    }
  };

  const fallbackWebSpeech = () => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;
    const recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.lang = "en-US";
    recognition.onresult = (e) => {
      const transcript = e.results[0]?.[0]?.transcript;
      if (transcript) setValue((prev) => `${prev} ${transcript}`.trim());
    };
    recognition.start();
  };

  return (
    <form onSubmit={submit} className="rounded-2xl border border-stone-800 bg-[#161413] p-2 shadow-sm transition-all focus-within:border-stone-700">
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
      
      {/* Top action pill toolbar */}
      <div className="flex items-center gap-1.5 pb-2 mb-1.5 border-b border-stone-800/60 px-1">
        <select
          value={importMode}
          onChange={(event) => setImportMode(event.target.value === "replace" ? "replace" : "append")}
          className="h-7 rounded-full border border-stone-800 bg-stone-900 px-2.5 text-[11px] text-stone-300 outline-none hover:border-stone-700 transition"
          aria-label="Import mode"
        >
          <option value="append">Append</option>
          <option value="replace">Replace</option>
        </select>

        <Button type="button" variant="ghost" size="sm" onClick={openFilePicker} className="h-7 px-2.5 text-xs text-stone-300 hover:text-white">
          <Upload className="h-3.5 w-3.5" />
          <span>Import</span>
        </Button>

        <Button type="button" variant="ghost" size="sm" onClick={openFilePicker} className="h-7 px-2.5 text-xs text-stone-300 hover:text-white">
          <FileSpreadsheet className="h-3.5 w-3.5" />
          <span>CSV/Excel</span>
        </Button>

        <div className="flex-1" />

        <Button type="button" variant="ghost" size="sm" onClick={onReset} disabled={disabled} className="h-7 px-2 text-xs text-stone-500 hover:text-stone-300" title="Reset Session">
          <RotateCcw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Input & Record Line */}
      <div className="flex min-h-10 items-center gap-2 px-1">
        {recording ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 px-2 text-xs text-rose-300">
            <span className="h-2 w-2 animate-ping rounded-full bg-rose-400" />
            <span className="font-medium">Listening via Deepgram Nova-3</span>
            <span className="text-stone-500">({recordSeconds}s)</span>
          </div>
        ) : transcribing ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 px-2 text-xs text-purple-300">
            <span className="h-2 w-2 animate-spin rounded-full border-2 border-purple-300 border-t-transparent" />
            <span className="font-medium">Transcribing speech...</span>
          </div>
        ) : (
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="Type or speak a dispatch request..."
            className="min-w-0 flex-1 bg-transparent px-2 text-[14px] text-stone-100 outline-none placeholder:text-stone-500"
          />
        )}

        <Button
          type="button"
          variant={recording ? "danger" : "secondary"}
          size="icon"
          aria-label="Voice"
          onClick={toggleRecording}
          disabled={!speechSupported || transcribing}
          className={`h-8 w-8 shrink-0 transition-transform ${recording ? "animate-pulse" : ""}`}
          title={speechSupported ? (recording ? "Stop Recording" : "Voice Input (Deepgram Nova)") : "Microphone not available"}
        >
          {recording ? <Square className="h-3.5 w-3.5 fill-current" /> : <Mic className="h-3.5 w-3.5 text-stone-300" />}
        </Button>

        <Button
          type="submit"
          variant="default"
          size="icon"
          disabled={disabled || !value.trim() || recording || transcribing}
          aria-label="Send"
          className="h-8 w-8 shrink-0 bg-white text-stone-950 hover:bg-stone-200"
        >
          <Send className="h-3.5 w-3.5" />
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
