from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video/<int:video_id>')
def play_video(video_id):
    # Assuming you have Cloudinary video URLs stored in a list
    video_urls = [
        "https://res.cloudinary.com/douekreel/video/upload/v1696499862/l42jbodn7f6svdgwnq4u.mp4",
        "https://res.cloudinary.com/douekreel/video/upload/v1696499683/lhvxzskuqxvck7okxzbt.mp4",
        "https://res.cloudinary.com/douekreel/video/upload/v1696499661/wiwyafu3roaimxkxv8ag.mp4",
        "https://res.cloudinary.com/douekreel/video/upload/v1696499609/rpi0pdkibg9rvodxgwzc.mp4",
        "https://res.cloudinary.com/douekreel/video/upload/v1696489890/Home_Video_No_Text__9_secs_1_o9nrrb.mp4"
    ]
    # Validate the video_id to prevent index out of range errors
    if 1 <= video_id <= len(video_urls):
        video_url = video_urls[video_id - 1]
        return render_template('videos.html', video_url=video_url)
    else:
        return "Invalid Video ID"


if __name__ == '__main__':
    app.run(debug=True)