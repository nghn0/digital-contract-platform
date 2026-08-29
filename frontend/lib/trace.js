export const traceLog = (msg) => {
  if (typeof window !== 'undefined') {
    fetch('/api/log', {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: msg})
    }).catch(()=>console.log(msg));
  } else {
    console.log(msg);
  }
}
