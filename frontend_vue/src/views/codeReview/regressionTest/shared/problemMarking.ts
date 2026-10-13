const STORAGE_PREFIX = 'codeReviewMarking';

type ProblemEntry = {
  problem: any;
  key: string;
};

export function buildProblemKey(problem: any): string {
  // 确保返回字符串类型
  const key = problem.id ||
    `${problem.issue_name || ''}-${problem.file_name || ''}-${problem.function_name || ''}-${problem.description_location || ''}`;
  
  // 如果是数字，转换为字符串
  return String(key);
}

function storageKey(taskId: string | number, analysisType: string) {
  return `${STORAGE_PREFIX}:${analysisType}:${taskId}`;
}

export function loadMarkedProblems(taskId: string | number, analysisType: string) {
  try {
    const data = localStorage.getItem(storageKey(taskId, analysisType));
    if (!data) return { markedSet: new Set(), problemsMap: new Map() };
    const parsed = JSON.parse(data);
    const markedSet = new Set(parsed.keys || []);
    const problemsMap = new Map(parsed.entries || []);
    return { markedSet, problemsMap };
  } catch (error) {
    console.error('加载标记问题失败', error);
    return { markedSet: new Set(), problemsMap: new Map() };
  }
}

export function saveMarkedProblem(taskId: string | number, analysisType: string, entry: ProblemEntry) {
  const { markedSet, problemsMap } = loadMarkedProblems(taskId, analysisType);
  markedSet.add(entry.key);
  problemsMap.set(entry.key, entry.problem);
  localStorage.setItem(storageKey(taskId, analysisType), JSON.stringify({
    keys: Array.from(markedSet),
    entries: Array.from(problemsMap.entries())
  }));
}

export function removeMarkedProblem(taskId: string | number, analysisType: string, key: string) {
  const { markedSet, problemsMap } = loadMarkedProblems(taskId, analysisType);
  markedSet.delete(key);
  problemsMap.delete(key);
  localStorage.setItem(storageKey(taskId, analysisType), JSON.stringify({
    keys: Array.from(markedSet),
    entries: Array.from(problemsMap.entries())
  }));
}

export function getMarkedProblemSet(taskId: string | number, analysisType: string) {
  const { markedSet } = loadMarkedProblems(taskId, analysisType);
  return markedSet;
}

export function getMarkedProblems(taskId: string | number, analysisType: string) {
  const { problemsMap } = loadMarkedProblems(taskId, analysisType);
  return Array.from(problemsMap.values());
}

export function getMarkedProblemEntries(taskId: string | number, analysisType: string) {
  const { problemsMap } = loadMarkedProblems(taskId, analysisType);
  return Array.from(problemsMap.entries()).map(([key, problem]) => ({ key, problem }));
}

export function getMarkedProblemKeys(taskId: string | number, analysisType: string) {
  const { markedSet } = loadMarkedProblems(taskId, analysisType);
  return markedSet;
}

export function clearMarkedProblems(taskId: string | number, analysisType: string) {
  localStorage.removeItem(storageKey(taskId, analysisType));
}