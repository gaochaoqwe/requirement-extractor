export const DRAFT_DB_NAME = 'test_case_assistant_db'
export const DRAFT_STORE_NAME = 'drafts'

export const openDraftDb = () => {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DRAFT_DB_NAME, 1)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(DRAFT_STORE_NAME)) {
        db.createObjectStore(DRAFT_STORE_NAME)
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export const draftSet = async (key, value) => {
  const db = await openDraftDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE_NAME, 'readwrite')
    const store = tx.objectStore(DRAFT_STORE_NAME)
    store.put(value, key)
    tx.oncomplete = () => {
      db.close()
      resolve()
    }
    tx.onerror = () => {
      db.close()
      reject(tx.error)
    }
  })
}

export const draftGet = async (key) => {
  const db = await openDraftDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE_NAME, 'readonly')
    const store = tx.objectStore(DRAFT_STORE_NAME)
    const req = store.get(key)
    req.onsuccess = () => {
      db.close()
      resolve(req.result)
    }
    req.onerror = () => {
      db.close()
      reject(req.error)
    }
  })
}

export const draftDel = async (key) => {
  const db = await openDraftDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE_NAME, 'readwrite')
    const store = tx.objectStore(DRAFT_STORE_NAME)
    store.delete(key)
    tx.oncomplete = () => {
      db.close()
      resolve()
    }
    tx.onerror = () => {
      db.close()
      reject(tx.error)
    }
  })
}
