export async function handleFetchError(response, fallbackMessage) {
  let message = fallbackMessage;
  try {
    const data = await response.json();
    if (data && data.detail) {
      message = data.detail;
    }
  } catch (e) {
    // ignore parse failure, use fallback
  }
  return new Error(message);
}
