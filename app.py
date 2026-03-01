export default async function handler(req, res) {
  const API_KEY = process.env.GEMINI_API_KEY; 
  const { rowData } = req.body;

  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ 
        parts: [{ 
          text: `You are a Senior RBI Compliance Officer. Audit this bank record specifically against the 7 Sutras (Trust, Fairness, Accountability, Safety, Transparency, Innovation, Human-Centricity). Data: ${rowData}. Provide a 2-sentence expert verdict.` 
        }] 
      }]
    })
  });

  const data = await response.json();
  res.status(200).json(data);
}
