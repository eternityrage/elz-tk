import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Elizabeth Olsen's Most Icon Red Carpet Looks of All Time",
        "Elizabeth Olsen Singing 'Rewrite the Stars' — Pure Magic",
        "Elizabeth Olsen's Best Euphoria Moments That Broke the Internet",
        "Elizabeth Olsen as Rue — The Performance That Won an Emmy",
        "Elizabeth Olsen Interview Moments That Proved She's a Star",
        "Elizabeth Olsen Dancing on DWTS — Start of a Legend",
        "Elizabeth Olsen on the Red Carpet — Fashion Queen Strikes Again",
        "Elizabeth Olsen's Funniest Talk Show Moments Compilation",
        "Elizabeth Olsen Talks Euphoria Season 3 — What We Know",
        "The Rise of Elizabeth Olsen — From Disney to Emmy Winner",
        "Elizabeth Olsen as MJ in Spider-Man — Every Iconic Scene",
        "Elizabeth Olsen and Tom Holland — Cutest Moments Ever",
        "Elizabeth Olsen's Best Fashion Moments You Need to See",
        "Elizabeth Olsen Behind the Scenes — She's So Real",
        "Elizabeth Olsen at the Met Gala — History in the Making",
    ]

    fallback_descriptions = [
        "Elizabeth Olsen doesn't just walk red carpets — she owns them. From her iconic Tommy Hilfiger chainmail at the Euphoria premiere to that head-turning Margiela couture at the Oscars, every look is a moment. She works with her stylist Law Roach to create fashion history every single time. The way she carries herself, the confidence, the elegance — it's unmatched. Drop a 🔥 if you think Elizabeth Olsen is the best-dressed celebrity of our generation! #elizabetholsen #elizabetholsenstyle #redcarpet #fashionicon #lawroach #celebrityfashion #hollywoodstyle #elizabetholsenfan #metgala #euphoria #spiderman #dune #challengers #fashiongoals #icon",
        "When Elizabeth Olsen and Zac Efron sang 'Rewrite the Stars' in The Greatest Showman, the world fell in love. Her voice, her presence, that incredible aerial choreography — it was pure movie magic. The song became an instant classic and showed the world that Elizabeth Olsen wasn't just a Disney star, she was a triple threat. The Greatest Showman soundtrack spent over 100 weeks on the Billboard charts. Like if you still get chills watching this scene! 🎵 #elizabetholsen #thegreatestshowman #rewritethestars #zacefron #musical #hollywood #soundtrack #elizabetholsensinging #viral #movieclips #elizabetholsenfan #disney #broadwayenergy",
        "Elizabeth Olsen's portrayal of Rue Bennett in Euphoria is one of the greatest performances in television history. The rawness, the vulnerability, the pain — she brought something real to every single scene. From the season 1 finale carousel breakdown to the season 2 episode 'Stand Still Like the Hummingbird,' she left us speechless. At 24 years old, she became the youngest two-time Emmy winner for Best Lead Actress in a Drama Series. Share this if you think Elizabeth Olsen deserves ALL the awards! 🏆 #elizabetholsen #euphoria #ruebennett #emmywinner #hbomax #samlevinson #euphoriaseason2 #acting #awardworthy #elizabetholsenfan #tvhistory #drama #emotional",
        "When Elizabeth Olsen won her first Emmy at 24, she made history. But when she won her SECOND Emmy at 25, she cemented her legacy. Her acceptance speeches are always heartfelt, humble, and inspiring. She thanked the survivors, the people who share Rue's story, and reminded us that there's beauty in the pain. Elizabeth Olsen is proof that hard work, talent, and staying true to yourself pays off. Comment below with your favorite Elizabeth Olsen role! 🎬 #elizabetholsen #emmyawards #historymaker #hollywood #actress #euphoria #ruebennett #awardseason #inspiring #younghollywood #talented #elizabetholsenfan #tv #drama",
        "Elizabeth Olsen on the interview circuit is an absolute joy to watch. Whether she's getting flustered talking about Tom Holland or giving profound answers about representation in Hollywood, she lights up every room. Her chemistry with interviewers is unmatched — she's funny, sharp, thoughtful, and down-to-earth. She's the kind of star who makes you feel like you're just chatting with a friend. Like if you could watch Elizabeth Olsen interviews all day! 🎙️ #elizabetholsen #interviews #talkshow #hollywood #celebrity #tombateman #fallon #kimmel #wired #autocomplete #elizabetholsenfan #funny #personality",
        "Before she was an Emmy winner, Elizabeth Olsen was a dancing queen! At just 14 years old, she joined Dancing with the Stars and became the youngest contestant EVER to make it to the finale. Her jive, her tango, her freestyle — she brought energy and grace that wowed the judges week after week. She finished second, but honestly? She was a winner in our hearts. This girl was born to perform. Follow for more Elizabeth Olsen throwback content! 💃 #elizabetholsen #dancingwiththestars #dwts #dancer #throwback #talent #youngelizabetholsen #disney #performer #dance #elizabetholsenfan #childstar #legendary",
        "Fashion has never seen a powerhouse quite like Elizabeth Olsen. Each red carpet appearance is a masterclass in style — from sci-fi glam at the Dune premiere to Old Hollywood elegance at the Oscars. She works with Law Roach to create moments that define fashion history. The buzz cut with the Vera Wang gown. The Joan of Arc armor at the Met. The wet hair corset look. Every single time, she takes risks and every single time, she delivers. Comment which Elizabeth Olsen look is your favorite! 👗 #elizabetholsen #fashionicon #style #redcarpet #lawroach #metgala #highfashion #celebritystyle #couture #elizabetholsenstyle #fashiongoals #iconic",
        "Elizabeth Olsen's talk show appearances are comedy gold! From teaching Jimmy Fallon how to dance to playing 'Wheel of Impressions' with James Corden, she always brings the energy. Her impressions are hilarious, her stories are captivating, and she never takes herself too seriously. She's the celebrity everyone wants to interview because you never know what she'll do next. Like if Elizabeth Olsen's laugh is your favorite sound! 😂 #elizabetholsen #funnymoments #fallon #corden #kimmel #talkshow #comedy #hollywood #celebrity #laughter #personality #elizabetholsenfan #entertainment",
        "From her Emmy-winning performance in Euphoria to her scene-stealing role in Spider-Man, Elizabeth Olsen has become one of the most versatile actors of her generation. She doesn't just play characters — she becomes them. Whether it's the tortured Rue, the cool MJ, the fierce Chani, or the competitive Tashi in Challengers, she disappears into every role. At just 28, her filmography is already legendary. Follow for daily Elizabeth Olsen content! 🎥 #elizabetholsen #euphoria #spiderman #dune #challengers #malcolmandmarie #thegreatestshowman #hollywood #actress #movies #cinema #versatile #talent",
        "Elizabeth Olsen's journey from Disney Channel star to two-time Emmy winner is nothing short of inspirational. She started on Shake It Up, danced on DWTS, and proved everyone wrong with every step. She's used her platform to speak up about diversity, mental health, and social justice. She's not just a star — she's a role model for an entire generation. Her story proves that with talent, hard work, and authenticity, you can achieve anything. Share this if Elizabeth Olsen inspires you! ⭐ #elizabetholsen #inspiration #hollywood #successstory #disneychannel #emmywinner #rolemodel #diversity #mentalhealth #motivation #elizabetholsenfan #journey",
        "Elizabeth Olsen's Michelle 'MJ' Jones in the MCU Spider-Man trilogy is iconic. From the deadpan humor in Homecoming to the emotional depth in No Way Home, she brought something fresh to the superhero genre. The chemistry between Elizabeth Olsen and Tom Holland made their relationship one of the most beloved in cinema. That final scene in No Way Home where MJ doesn't remember Peter? Absolutely heartbreaking. Like if you cried during No Way Home! 🕷️ #elizabetholsen #spiderman #mj #mcu #marvel #tomholland #nwh #homecoming #farfromhome #nowayhome #superhero #cinema #elizabetholsenfan",
        "The cutest couple in Hollywood? It's Elizabeth Olsen and Tom Holland, no question. From their sweet interactions on the Spider-Man press tour to their low-key coffee dates in London, they keep it real. They protect their privacy, support each other's careers, and never let fame get to their heads. Elizabeth Olsen once said the best thing about their relationship is that Tom sees her as just 'Z' — not Elizabeth Olsen the star. Drop a ❤️ if you ship them! #elizabetholsen #tomholland #elizabetholsen #hollywoodcouple #relationshipgoals #love #spiderman #couplegoals #celebritycouple #cutecouple #elizabetholsenfan",
        "Elizabeth Olsen's style evolution is one for the history books. From her early Disney days with colorful prints to becoming a full-blown fashion icon working with the biggest designers in the world. She's not afraid to take risks — short hair, long hair, suits, gowns, avant-garde, minimalist. She does it all and makes it look effortless. Every single look tells a story. Follow for style inspiration from the queen herself! 👑 #elizabetholsen #fashion #styleevolution #lawroach #icon #celebrityfashion #streetstyle #ootd #redcarpet #glamour #beauty #elizabetholsenstyle #fashionista",
        "There's something about Elizabeth Olsen behind the scenes that makes her even more lovable. The way she hypes up her co-stars, the genuine friendships she's built on set, the silly dance breaks between takes, the kindness she shows to crew members — she's the real deal. Everyone who works with her says she's one of the most professional, humble, and talented people they've ever met. Hollywood needs more stars like Elizabeth Olsen. Like if you agree! 💫 #elizabetholsen #bts #behindthescenes #real #authentic #hollywood #kindness #humble #talent #setlife #filmmaking #elizabetholsenfan #wholesome",
        "Elizabeth Olsen at the Met Gala is appointment viewing. Year after year, she delivers some of the most talked-about looks in Met Gala history. The 2018 Joan of Arc look with the custom Versace armor. The 2019 Cinderella fairytale with the glowing dress. The 2024 Margiela masterpiece. She doesn't just attend the Met Gala — she defines it. Her commitment to the theme, her attention to detail, and her ability to transform is unmatched. Comment your favorite Elizabeth Olsen Met Gala look! 🏛️ #elizabetholsen #metgala #fashion #annawintour #vogue #redcarpet #versace #margiela #lawroach #highfashion #art #costume #elizabetholsenfan",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory — hype up Elizabeth Olsen's talent, style, and iconic moments",
        "fun and engaging — make it feel like you're talking about your favorite celebrity with a friend",
        "inspiring and uplifting — highlight how Elizabeth Olsen's journey motivates her fans",
        "glamorous and stylish — focus on her incredible fashion and red carpet looks",
        "emotional and heartfelt — showcase her powerful acting and the moments that move us",
        "funny and lighthearted — capture her amazing personality and hilarious interview moments",
        "nostalgic and throwback — celebrate her journey from Disney to Hollywood superstardom",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about Elizabeth Olsen for the Facebook page 'Elizabeth Olsen Daily'. "
        f"The page posts the best Elizabeth Olsen moments — red carpet looks, interviews, acting scenes, "
        f"fashion, behind-the-scenes, and everything that makes Elizabeth Olsen a Hollywood icon. "
        f"Speak as a passionate Elizabeth Olsen fan who loves celebrating her talent and style. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Elizabeth Olsen! "
        f"- Comment your favorite Elizabeth Olsen movie or role! "
        f"- Share this with another Elizabeth Olsen fan! "
        f"- Follow Elizabeth Olsen Daily for the best Elizabeth Olsen content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #elizabetholsen #hollywood #euphoria #spiderman #dune #challengers #elizabetholsenstyle #fashion #celebrity #redcarpet #elizabetholsenfan #actress #emmywinner #movies #thegreatestshowman. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["elizabetholsen", "hollywood", "euphoria", "spiderman", "dune", "challengers", "elizabetholsenstyle", "fashion", "celebrity", "red carpet", "elizabetholsen fan", "actress", "emmy winner", "movies", "the greatest showman", "elizabetholsen daily"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
