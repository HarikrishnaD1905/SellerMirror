from mistralai.client import Mistral  # type: ignore
from dotenv import load_dotenv  # type: ignore
import os

load_dotenv(override=True)
client = Mistral(api_key=os.getenv('MISTRAL_API_KEY'))

def build_context(pipeline_output):
    scores = pipeline_output.get('scores', {})
    cm = pipeline_output.get('comparison', {}).get('complaint_mirror', {})
    tg = pipeline_output.get('comparison', {}).get('trust_gap', {})
    ms = pipeline_output.get('comparison', {}).get('momentum', {})
    alert = pipeline_output.get('alert', {})

    my_wins = cm.get('winner_per_category', {})
    my_win_cats = [k for k,v in my_wins.items() if v == 'my_product']
    comp_win_cats = [k for k,v in my_wins.items() if v == 'competitor']

    return f"""
MARKET INTELLIGENCE REPORT
===========================
My Product Health: {int(scores.get('health', 0))}/100
Competitor Vulnerability: {int(scores.get('vulnerability', 0))}/100

COMPARISON RESULTS:
- Complaint Matchup (Who gets fewer complaints): I win on {my_win_cats}. Competitor wins on {comp_win_cats}.
  My complaints: {cm.get('my_complaint_counts', {})}
  Competitor complaints: {cm.get('comp_complaint_counts', {})}
- Customer Trust (Who keeps customers happier): Winner = {tg.get('winner', 'unknown')}
  My repeat customers: {tg.get('my_repeat_rate', 0):.0%}
  Competitor rating trend: {tg.get("comp_rating_vel_mean", 0):.1f} stars per week
- Momentum (Is the competitor panicking?): Momentum lost = {ms.get("momentum_lost", False)}
  Consecutive days dropping price: {ms.get("price_drop_streak_days", 0)} days
  Are they getting fewer reviews? {ms.get("review_volume_decline", False)}

ALERT STATUS: {alert.get('alert_level', '').upper()}
Title: {alert.get('alert_title', '')}
Confidence: {alert.get('confidence_pct', 0)}%
Reasoning: {alert.get('conditions_summary', '')}
Recommended actions: {alert.get('alert_message', '')}
"""

def ask_agent(question, pipeline_output, system_prompt=None, max_tokens=800):
    context = build_context(pipeline_output)
    prompt = context + f"\n\nSeller question: {question}"
    
    if not system_prompt:
        system_prompt = (
            "You are SellerMirror, a plain-spoken expert e-commerce strategy analyst. "
            "Explain things simply so anyone can understand. Avoid overly complex numbers, and use clear language. "
            "Highlight what matters. Aim for responses around 300 words.Use headings, sub-headings and bullet points to make the response more readable."
        )

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def generate_market_report(pipeline_output):
    report_prompt = (
        "You are the SellerMirror Chief Strategy Officer. Write a high-impact, "
        "3-point strategic summary based on the provided data.\n"
        "FORMATTING RULES:\n"
        "- Use markdown strictly.\n"
        "- Start with a very short, punchy executive summary sentence.\n"
        "- Use **bolding** for the 3 main points and start each with a relevant emoji.\n"
        "- Ground EVERY point in specific data from the context (e.g. quote exact scores, counts, or rates).\n"
        "- Add a concluding 'Immediate Actions' bulleted list.\n"
        "- Keep it under 250 words total. Be ruthless, sharp, and highly actionable."
    )
    return ask_agent(
        "Based on this market data, provide a premium 3-point strategic summary "
        "of my current situation and immediate priorities.",
        pipeline_output,
        system_prompt=report_prompt,
        max_tokens=800
    )

if __name__ == '__main__':
    sample = {
        'scores': {'health': 45.0, 'vulnerability': 53.9},
        'comparison': {
            'complaint_mirror': {
                'winner_per_category': {'quality': 'my_product', 'listing': 'competitor'},
                'my_complaint_counts': {'quality': 8, 'listing': 9},
                'comp_complaint_counts': {'quality': 13, 'listing': 1}
            },
            'trust_gap': {'winner': 'my_product', 'my_repeat_rate': 0.36, 'comp_rating_velocity': -0.32},
            'momentum': {'momentum_lost': True, 'price_drop_streak': 7, 'review_volume_decline': True}
        },
        'alert': {
            'alert_level': 'red',
            'alert_title': 'Strike Now — High Confidence Opportunity Detected',
            'confidence_pct': 80,
            'conditions_summary': '4 of 5 signals converging',
            'alert_message': 'Hold your price. Push visibility now.'
        }
    }
    print('Testing SellerMirror Strategy Agent...')
    print(generate_market_report(sample))
