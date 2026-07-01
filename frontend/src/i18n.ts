import type { Locale, PageId } from "./types";

type TextKey =
  | "brand"
  | "home"
  | "settings"
  | "logs"
  | "engine"
  | "account"
  | "balance"
  | "botComparison"
  | "botName"
  | "closedProfit"
  | "positions"
  | "pnl"
  | "exposure"
  | "nextAction"
  | "runtime"
  | "runControls"
  | "operatorSettings"
  | "localLifecycle"
  | "developerUpdate"
  | "firstRun"
  | "guidedPath"
  | "exchange"
  | "apiKey"
  | "apiSecret"
  | "leverage"
  | "recommendedLeverage"
  | "walletBalance"
  | "allocatedAmount"
  | "marketMode"
  | "spot"
  | "futures"
  | "intent"
  | "dryRun"
  | "live"
  | "testnet"
  | "preview"
  | "apply"
  | "validate"
  | "saveDraft"
  | "config"
  | "language"
  | "fetch"
  | "openProfit"
  | "runtimeSafe"
  | "summary"
  | "trades"
  | "liveSafetyNote"
  | "recentEvents"
  | "eventTape"
  | "severity"
  | "lookup"
  | "supportReport"
  | "update"
  | "pairlist"
  | "loading"
  | "empty"
  | "walletSyncPending"
  | "walletSynced"
  | "winLoss"
  | "readOnly";

const DICTIONARY: Record<Locale, Record<TextKey, string>> = {
  en: {
    brand: "NFI Engine",
    home: "Home",
    settings: "Settings",
    logs: "Logs",
    engine: "Engine",
    account: "Account",
    balance: "Balance",
    botComparison: "Bot comparison",
    botName: "Bot Name",
    closedProfit: "Closed Profit",
    positions: "Positions",
    pnl: "PnL",
    exposure: "Exposure",
    nextAction: "Next action",
    runtime: "Runtime",
    runControls: "Run controls",
    operatorSettings: "Local operator settings",
    localLifecycle: "Local data lifecycle",
    developerUpdate: "Developer update",
    firstRun: "First-run setup",
    guidedPath: "Guided path",
    exchange: "Exchange",
    apiKey: "API key",
    apiSecret: "API secret",
    leverage: "Leverage",
    recommendedLeverage: "3x recommended",
    walletBalance: "Wallet balance",
    allocatedAmount: "Allocated amount",
    marketMode: "Market mode",
    spot: "Spot",
    futures: "Futures",
    intent: "Run intent",
    dryRun: "Dry run",
    live: "Live",
    testnet: "Testnet",
    preview: "Preview",
    apply: "Apply",
    validate: "Validate",
    saveDraft: "Save draft",
    config: "Config",
    language: "Language",
    fetch: "Fetch",
    openProfit: "Open Profit",
    runtimeSafe: "Runtime safe",
    summary: "Summary",
    trades: "Trades",
    liveSafetyNote: "Live requires confirm, preflight, limit review, kill switch, and reconciliation proof.",
    recentEvents: "Recent events",
    eventTape: "Event tape",
    severity: "Severity",
    lookup: "Lookup",
    supportReport: "Support report",
    update: "Update",
    pairlist: "Pairlist",
    loading: "Loading",
    empty: "No runtime snapshot yet. Complete settings or start dry run first.",
    walletSyncPending: "wallet sync pending",
    walletSynced: "wallet synced",
    winLoss: "W/L",
    readOnly: "Read-only mode",
  },
  ko: {
    brand: "NFI Engine",
    home: "홈",
    settings: "설정",
    logs: "로그",
    engine: "엔진",
    account: "계좌",
    balance: "잔고",
    botComparison: "봇 비교",
    botName: "봇 이름",
    closedProfit: "종료 손익",
    positions: "포지션",
    pnl: "손익",
    exposure: "노출",
    nextAction: "다음 행동",
    runtime: "런타임",
    runControls: "실행 제어",
    operatorSettings: "로컬 운영자 설정",
    localLifecycle: "로컬 데이터 관리",
    developerUpdate: "개발자 업데이트",
    firstRun: "첫 실행 설정",
    guidedPath: "가이드 설정",
    exchange: "거래소",
    apiKey: "API 키",
    apiSecret: "API 시크릿",
    leverage: "레버리지",
    recommendedLeverage: "3x 권장",
    walletBalance: "지갑 잔고",
    allocatedAmount: "투입 금액",
    marketMode: "시장 모드",
    spot: "현물",
    futures: "선물",
    intent: "실행 의도",
    dryRun: "드라이런",
    live: "실전",
    testnet: "테스트넷",
    preview: "미리보기",
    apply: "적용",
    validate: "검증",
    saveDraft: "초안 저장",
    config: "구성",
    language: "언어",
    fetch: "잔고 조회",
    openProfit: "오픈 손익",
    runtimeSafe: "안전 구성",
    summary: "요약",
    trades: "거래",
    liveSafetyNote: "Live는 confirm, preflight, limit review, kill switch, reconciliation proof 이후에만 가능합니다.",
    recentEvents: "최근 이벤트",
    eventTape: "이벤트 테이프",
    severity: "심각도",
    lookup: "조회",
    supportReport: "지원 리포트",
    update: "업데이트",
    pairlist: "페어 목록",
    loading: "불러오는 중",
    empty: "아직 런타임 스냅샷이 없습니다. 먼저 설정을 완료하거나 드라이런을 시작하세요.",
    walletSyncPending: "지갑 동기화 대기",
    walletSynced: "지갑 동기화됨",
    winLoss: "W/L",
    readOnly: "읽기 전용 모드",
  },
  el: {
    brand: "NFI Engine",
    home: "Αρχική",
    settings: "Ρυθμίσεις",
    logs: "Αρχεία",
    engine: "Μηχανή",
    account: "Λογαριασμός",
    balance: "Υπόλοιπο",
    botComparison: "Σύγκριση bot",
    botName: "Όνομα bot",
    closedProfit: "Κλειστό κέρδος",
    positions: "Θέσεις",
    pnl: "PnL",
    exposure: "Έκθεση",
    nextAction: "Επόμενη ενέργεια",
    runtime: "Χρόνος εκτέλεσης",
    runControls: "Έλεγχος λειτουργίας",
    operatorSettings: "Τοπικές ρυθμίσεις χειριστή",
    localLifecycle: "Τοπική διαχείριση δεδομένων",
    developerUpdate: "Ενημέρωση προγραμματιστή",
    firstRun: "Ρύθμιση πρώτης εκτέλεσης",
    guidedPath: "Οδηγός ρύθμισης",
    exchange: "Ανταλλακτήριο",
    apiKey: "Κλειδί API",
    apiSecret: "Μυστικό API",
    leverage: "Μόχλευση",
    recommendedLeverage: "3x προτεινόμενο",
    walletBalance: "Υπόλοιπο πορτοφολιού",
    allocatedAmount: "Ποσό χρήσης",
    marketMode: "Λειτουργία αγοράς",
    spot: "Spot",
    futures: "Συμβόλαια",
    intent: "Πρόθεση εκτέλεσης",
    dryRun: "Δοκιμή",
    live: "Ζωντανά",
    testnet: "Testnet",
    preview: "Προεπισκόπηση",
    apply: "Εφαρμογή",
    validate: "Έλεγχος",
    saveDraft: "Αποθήκευση πρόχειρου",
    config: "Ρύθμιση",
    language: "Γλώσσα",
    fetch: "Ανάκτηση",
    openProfit: "Ανοιχτό κέρδος",
    runtimeSafe: "Ασφαλής λειτουργία",
    summary: "Σύνοψη",
    trades: "Συναλλαγές",
    liveSafetyNote: "Το Live απαιτεί confirm, preflight, limit review, kill switch και reconciliation proof.",
    recentEvents: "Πρόσφατα γεγονότα",
    eventTape: "Ταινία γεγονότων",
    severity: "Σοβαρότητα",
    lookup: "Αναζήτηση",
    supportReport: "Αναφορά υποστήριξης",
    update: "Ενημέρωση",
    pairlist: "Λίστα ζευγών",
    loading: "Φόρτωση",
    empty: "Δεν υπάρχει ακόμη στιγμιότυπο. Ολοκληρώστε τις ρυθμίσεις ή ξεκινήστε δοκιμή.",
    walletSyncPending: "αναμονή συγχρονισμού",
    walletSynced: "συγχρονίστηκε",
    winLoss: "W/L",
    readOnly: "Λειτουργία μόνο ανάγνωσης",
  },
};

export function normalizeLocale(raw: string | null | undefined): Locale {
  if (raw === "ko" || raw === "el" || raw === "en") {
    return raw;
  }
  return "en";
}

export function text(locale: Locale, key: TextKey): string {
  return DICTIONARY[locale][key];
}

export function pageTitle(locale: Locale, page: PageId): string {
  const titles: Record<PageId, TextKey> = {
    home: "brand",
    settings: "operatorSettings",
    logs: "recentEvents",
  };
  return `${text(locale, titles[page])} · NFI`;
}
