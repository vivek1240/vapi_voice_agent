#!/usr/bin/env python3
"""
Test Script for Best Buy Call Evaluator

Run this script to test the evaluation system locally with sample transcripts.

Usage:
    python scripts/test_bestbuy_evaluator.py

Environment Variables Required:
    GROQ_API_KEY - Your Groq API key
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.bestbuy_call_evaluator import get_bestbuy_call_evaluator, BestBuyCallEvaluator


# Sample test transcripts
SAMPLE_TRANSCRIPTS = {
    "tv_display_resolved": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: Hi, my Samsung TV suddenly has no picture but I can still hear the audio.

Agent: I'm sorry to hear you're having trouble with your Samsung TV. Let's work together to get this sorted out. First, has the TV been dropped or experienced any physical damage recently?

Customer: No, nothing like that. It was working fine yesterday.

Agent: Good to know. Let's start with some basic troubleshooting. Could you try unplugging the TV from the wall outlet, wait about 30 seconds, and then plug it back in?

Customer: Okay, hold on... alright, I plugged it back in.

Agent: Great. Now turn it on and tell me what you see.

Customer: Still no picture, just black screen with sound.

Agent: Let's try another step. On your Samsung remote, press and hold the power button for about 10 seconds. This does a soft reset.

Customer: Doing that now... oh wait, the picture just came back!

Agent: Excellent! It looks like that did the trick. Is the picture displaying normally now?

Customer: Yes! It's working perfectly. That was easy!

Agent: I'm glad we got that working for you. Just so you know, this sometimes happens when the TV's internal processor gets stuck. If it happens again, try that same reset. Is there anything else I can help you with today?

Customer: No, that's all I needed. Thank you so much!

Agent: You're welcome! Thanks for calling Best Buy - have a great day!
""",

    "physical_damage_geeksquad": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: Yeah, I dropped my iPhone and now the screen is cracked and it won't turn on.

Agent: I'm sorry to hear about that. Let me ask a couple questions to understand the situation. When did this happen, and how far did it fall?

Customer: It happened this morning. It fell off my kitchen counter onto the tile floor.

Agent: I see. Is the screen completely shattered or just cracked? And you said it won't power on at all?

Customer: The screen has a big crack across it and some smaller cracks around the edges. Yeah, I've tried the power button and charging it but nothing happens.

Agent: Based on what you're describing - the cracked screen and the fact that it won't power on after the drop - this sounds like it needs hands-on attention that I can't provide over the phone. The impact may have damaged internal components.

Customer: So what do I do?

Agent: Our Geek Squad team can diagnose exactly what's wrong and repair it. Before I recommend next steps, do you have a Best Buy Protection Plan or AppleCare+ on this iPhone?

Customer: I have the Best Buy Protection Plan.

Agent: Great news! Your Protection Plan should cover accidental damage like this. Here's what I recommend: bring your iPhone to the nearest Best Buy with Geek Squad services. They'll do a full diagnostic, and since you have the Protection Plan, the repair costs should be covered, possibly with a deductible depending on your plan. Would you like me to help you find the nearest location?

Customer: Yes, please.

Agent: I can see there's a Best Buy with Geek Squad about 3 miles from your location. They're open today until 9 PM. When you go in, bring the phone, your charger, and your proof of purchase if you have it. They can look up your Protection Plan in the system.

Customer: Okay, I'll head over there today. Thanks for the help.

Agent: I'm sorry we couldn't fix this over the phone, but the Geek Squad team will take great care of you. Is there anything else I can help with?

Customer: No, that's it. Thanks.

Agent: You're welcome. Thanks for calling Best Buy, and I hope the repair goes smoothly!
""",

    "wifi_frustrated_resolved": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: I've been trying for two hours to get my new smart TV connected to Wi-Fi and it's not working. This is ridiculous.

Agent: I understand how frustrating that is, especially after spending two hours on it. Let's work through this together and get your TV connected. What brand and model is the TV?

Customer: It's an LG 55-inch. I just bought it from Best Buy last week.

Agent: Thanks. And just to confirm, other devices in your home are connecting to Wi-Fi without problems - like your phone or laptop?

Customer: Yes, everything else works fine. It's just this stupid TV.

Agent: That's actually helpful information - it tells us the issue is likely with the TV's connection to your router, not your internet itself. Let's try a few things. First, on the TV, go to Settings, then Network. What do you see there?

Customer: It shows my network name but says "Not Connected."

Agent: Good. Select your network and try entering the password again. Sometimes a small typo can cause this.

Customer: I've entered it like five times already. I know it's right.

Agent: I believe you. Let's try something else. On your TV, go to Settings, Network, and look for an option that says "Reset Network" or "Reset Network Settings." Do you see that?

Customer: Yeah, I see it.

Agent: Select that and confirm. This will clear any saved network data and let us start fresh.

Customer: Okay, done.

Agent: Now try connecting to your Wi-Fi network again with your password.

Customer: Entering the password now... oh my god, it's connecting. It says "Connected"!

Agent: Excellent! Let's verify it's working. Try opening a streaming app like Netflix or YouTube.

Customer: YouTube is loading... yes! It's working! I can't believe a reset fixed it. I wasted two hours trying everything else.

Agent: I'm glad we got it working. Sometimes the TV's network module just needs a fresh start. Is everything else on the TV working okay?

Customer: Yeah, it all looks good now. Thanks for your patience. I was pretty frustrated.

Agent: No problem at all - I completely understand. Is there anything else I can help you with today?

Customer: No, I'm good. Thanks again!

Agent: You're welcome! Thanks for calling Best Buy - enjoy your new TV!
""",

    "return_request": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: I want to return a laptop I bought two weeks ago.

Agent: I'd be happy to help you with that. Could you tell me a bit about why you're returning it? Is there an issue with the laptop, or is it just not what you needed?

Customer: It's just not powerful enough for what I need. The performance is too slow for my video editing software.

Agent: I understand - having the right specs for video editing is important. Since it's been two weeks, you're still within our return window. Most products can be returned within 15 days, or 60 days if you're a Total Tech member. Are you a Total Tech member?

Customer: No, just regular. So 15 days... is today okay?

Agent: Let me check - you said you bought it two weeks ago, so that would be 14 days. You should be just within the return period, but I'd recommend heading to the store today to be safe. Do you have the original receipt and all the accessories that came with the laptop?

Customer: I have the receipt and the box with everything in it.

Agent: Perfect. Just bring all of that to any Best Buy store and they can process the return for you. They'll inspect the laptop to make sure it's in good condition. Since you mentioned it wasn't powerful enough for video editing, would you like me to suggest some laptops that might be better suited for that when you go in?

Customer: Sure, that would help.

Agent: For video editing, I'd recommend looking at laptops with at least 16GB of RAM and a dedicated graphics card. The MacBook Pro, Dell XPS, and ASUS ProArt series are popular choices for video editors. When you're at the store, mention you're doing video editing and the team can help you find the right fit.

Customer: Okay, that's helpful. I'll head to the store now.

Agent: Sounds good. Is there anything else I can help you with today?

Customer: No, that's all. Thanks.

Agent: You're welcome. Thanks for calling Best Buy, and good luck finding the perfect laptop for your video editing!
""",

    "angry_customer_unresolved": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: This is the third time I'm calling about my washing machine! It's still broken and nobody is helping me!

Agent: I'm really sorry to hear you've had to call multiple times. That must be incredibly frustrating. Let me pull up your case and see what's been happening.

Customer: I've already explained this twice! The machine won't drain properly and my clothes come out soaking wet. I paid good money for this and it's garbage!

Agent: I completely understand your frustration. Let me take a fresh look at this. When did you first notice the draining issue?

Customer: It started two weeks ago. I was told a technician would come, but nobody ever showed up!

Agent: I apologize for that. Let me check the service schedule... I see a technician visit was scheduled but it looks like there was a scheduling conflict. That's unacceptable and I'm sorry.

Customer: I don't want excuses! I want my washing machine fixed or I want my money back!

Agent: You have every right to be upset. Here's what I can do - I can escalate this to our priority service team and get a technician to your home within the next 48 hours, or if you prefer, I can check your return eligibility given the ongoing issues.

Customer: I don't trust you'll actually send someone. I want to speak to a manager.

Agent: I understand. Let me connect you with a supervisor who can provide additional options and ensure this gets resolved. Please hold for just a moment while I transfer you.

Customer: Fine. But this better get fixed.

Agent: I'll make sure the supervisor has all the details about your case so you don't have to repeat yourself. One moment please.
""",

    "bluetooth_headphones": """
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: Hi, I just got some Sony headphones and I can't get them to pair with my iPhone.

Agent: No problem, I can help you with that. Are these the Sony WH-1000XM5 headphones or a different model?

Customer: Yeah, the XM5s. I've tried pairing them but my phone doesn't see them.

Agent: Let's get those connected. First, make sure the headphones are in pairing mode. Turn them off first, then press and hold the power button for about 7 seconds until you hear a voice prompt saying "Bluetooth pairing."

Customer: Okay, holding it now... I hear it say "Bluetooth pairing."

Agent: Perfect. Now on your iPhone, go to Settings, then Bluetooth. Make sure Bluetooth is turned on. Do you see "WH-1000XM5" in the list of available devices?

Customer: Let me look... yes! I see it now.

Agent: Great, tap on it to connect.

Customer: It says "Connected" now!

Agent: Excellent! Let's test it. Try playing some music or a video and tell me if you hear the audio through the headphones.

Customer: Playing something now... yes, I can hear it! The sound quality is amazing.

Agent: Perfect! The headphones are all set up. A quick tip - once they're paired like this, they'll usually connect automatically when you turn them on and have Bluetooth enabled on your phone. Is there anything else you'd like help with?

Customer: No, that was easy. Thank you!

Agent: You're welcome! Enjoy your new headphones. Thanks for calling Best Buy!
"""
}


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def print_evaluation(evaluation, transcript_name: str):
    """Pretty print an evaluation result."""
    print(f"📋 EVALUATION RESULTS: {transcript_name}")
    print("-" * 60)
    
    # Core Metrics
    print("\n🎯 CORE METRICS:")
    print(f"   Sentiment:     {evaluation.user_sentiment.value}")
    print(f"   Resolved:      {evaluation.query_resolved}")
    print(f"   Escalation:    {evaluation.escalation_required}")
    
    # Domain Metrics
    print("\n📦 DOMAIN METRICS:")
    print(f"   Issue:         {evaluation.issue_category.value}")
    print(f"   Product:       {evaluation.product_category.value}")
    print(f"   Resolution:    {evaluation.resolution_path.value}")
    
    # Efficiency Metrics
    print("\n⚡ EFFICIENCY METRICS:")
    print(f"   Tier:          {evaluation.troubleshooting_tier.value}")
    print(f"   FCR:           {evaluation.first_call_resolution}")
    
    # Quality Metrics
    print("\n✅ QUALITY METRICS:")
    print(f"   Diagnosis:     {evaluation.proper_diagnosis}")
    
    # Summary
    print("\n📝 SUMMARY:")
    print(f"   {evaluation.call_summary}")


def main():
    """Run the evaluation tests."""
    print("\n" + "🔵" * 40)
    print("\n  BEST BUY CALL EVALUATOR - LOCAL TEST")
    print("\n" + "🔵" * 40)
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GROQ_API_KEY environment variable not set!")
        print("\nTo set it, run:")
        print("  export GROQ_API_KEY='your-api-key-here'")
        print("\nGet a free API key at: https://console.groq.com/keys")
        sys.exit(1)
    
    print(f"\n✅ GROQ_API_KEY found (length: {len(api_key)})")
    
    # Initialize evaluator
    print("\n📡 Initializing evaluator...")
    evaluator = get_bestbuy_call_evaluator()
    
    if not evaluator.is_available():
        print("❌ Evaluator not available - check API key")
        sys.exit(1)
    
    print(f"   Model: {evaluator.model}")
    print(f"   Response format: {evaluator.response_format}")
    
    # Run evaluations
    results = []
    
    for name, transcript in SAMPLE_TRANSCRIPTS.items():
        print_separator()
        print(f"🎤 Evaluating transcript: {name}")
        print(f"   Length: {len(transcript)} characters")
        
        try:
            evaluation = evaluator.evaluate(transcript)
            
            if evaluation:
                print_evaluation(evaluation, name)
                results.append({
                    "name": name,
                    "success": True,
                    "evaluation": evaluation.model_dump()
                })
            else:
                print(f"❌ Evaluation returned None for {name}")
                results.append({
                    "name": name,
                    "success": False,
                    "error": "Evaluation returned None"
                })
                
        except Exception as e:
            print(f"❌ Error evaluating {name}: {e}")
            results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print_separator()
    print("📊 TEST SUMMARY")
    print("-" * 40)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"   Total tests:     {len(results)}")
    print(f"   ✅ Successful:    {successful}")
    print(f"   ❌ Failed:        {failed}")
    
    # Aggregate metrics from successful evaluations
    if successful > 0:
        print("\n📈 AGGREGATE METRICS:")
        
        # Sentiment distribution
        sentiments = {}
        for r in results:
            if r["success"]:
                s = r["evaluation"]["user_sentiment"]
                sentiments[s] = sentiments.get(s, 0) + 1
        print(f"   Sentiments: {sentiments}")
        
        # Resolution paths
        paths = {}
        for r in results:
            if r["success"]:
                p = r["evaluation"]["resolution_path"]
                paths[p] = paths.get(p, 0) + 1
        print(f"   Resolution paths: {paths}")
        
        # FCR rate
        fcr_count = sum(1 for r in results if r["success"] and r["evaluation"]["first_call_resolution"])
        print(f"   FCR rate: {fcr_count}/{successful} ({fcr_count/successful*100:.1f}%)")
        
        # Resolution rate
        resolved_count = sum(1 for r in results if r["success"] and r["evaluation"]["query_resolved"])
        print(f"   Resolution rate: {resolved_count}/{successful} ({resolved_count/successful*100:.1f}%)")
    
    # Save results to file
    output_file = f"data/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("data", exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    print_separator()
    print("🏁 Test complete!")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
