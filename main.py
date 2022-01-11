from pathlib import Path
from tkinter import *
from tkinter import Tk, Button, messagebox
from requests import get
from os import path, remove
from pygame import mixer
from PIL import ImageTk, Image
from threading import Thread
from random import shuffle
from re import sub
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3

root = Tk()

musicsList = []
isPaused = True
x = 0  # Current song index in musicsList
totalSonglength = 0
timeLastClic = 0
lastClicPos = 0
askSongAlreadyOpen = False
queueAlreadyOpen = False

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")


def GetFile(path: str) -> Path:
    return ASSETS_PATH / Path(path)


mixer.init()


def ValidFileName(string):
    string = str(string)
    badchars = '\\/:*?\"<>|'
    for ch in badchars:
        fileName = string.replace(ch, '')
    return fileName


def Queue():
    global x, musicsList
    pos = mixer.music.get_pos()
    if int(pos) == -1:
        if len(musicsList) > x+1:
            x += 1
            PlayMusic(musicsList[x])
        else:
            x = 0
            PlayMusic(musicsList[x])

    root.after(1, Queue)


def DownloadImage(name, imageURL):
    reponse = get(imageURL)
    file = open(name, "wb")
    file.write(reponse.content)
    file.close()


def UpdateGUI():
    global musicsList, x

    canvas.itemconfig(CurrentTitleText,
                      text=f"{musicsList[x].split(' § ')[-1][0:17]}")
    canvas.itemconfig(CurrentArtistText, text=musicsList[x].split(" § ")[0])

    request = get(
        f"https://api.deezer.com/search/track?q={musicsList[x].replace('§', '-')}").json()

    defaultImageURL = "https://images.assetsdelivery.com/compings_v2/pavelstasevich/pavelstasevich1902/pavelstasevich190200120.jpg"

    try:
        imageURL = request["data"][0]["album"]["cover_big"]
        DownloadImage("albumCover.png", imageURL)
    except:
        DownloadImage("albumCover.png", defaultImageURL)

    image = ImageTk.PhotoImage(Image.open("albumCover.png").resize((130, 129)))
    canvas.itemconfig(AlbumCover, image=image)
    canvas.albumCover = image
    remove("albumCover.png")

    try:
        imageURL = request["data"][0]["artist"]["picture_big"]
        DownloadImage("ArtistImage.png", imageURL)
    except:
        DownloadImage("ArtistImage.png", defaultImageURL)

    image = ImageTk.PhotoImage(Image.open("ArtistImage.png").resize((58, 58)))
    canvas.itemconfig(ArtistPicture, image=image)
    canvas.artistImg = image
    remove("ArtistImage.png")

    if len(musicsList) > x+1:
        canvas.itemconfig(NextArtistText, text=musicsList[x+1].split(" § ")[0])
        canvas.itemconfig(
            NextTitleText, text=f"{musicsList[x+1].split(' § ')[-1][0:15]}")

        try:
            request = get(
                f"https://api.deezer.com/search/track?q={musicsList[x+1].replace('§', '-')}").json()
            imageURL = request["data"][0]["album"]["cover_big"]
            DownloadImage("nextSongCover.png", imageURL)
        except:
            DownloadImage("nextSongCover.png", defaultImageURL)
    else:
        canvas.itemconfig(NextArtistText, text=musicsList[0].split(" § ")[0])
        canvas.itemconfig(
            NextTitleText, text=f"{musicsList[0].split(' § ')[-1][0:15]}")

        try:
            request = get(
                f"https://api.deezer.com/search/track?q={musicsList[0].replace('§', '-')}").json()
            imageURL = request["data"][0]["album"]["cover_big"]
            DownloadImage("nextSongCover.png", imageURL)
        except:
            DownloadImage("nextSongCover.png", defaultImageURL)

    image = ImageTk.PhotoImage(Image.open(
        "nextSongCover.png").resize((52, 52)))
    canvas.itemconfig(NextArtist, image=image)
    canvas.nextSongCover = image
    remove("nextSongCover.png")


def PlayMusic(MusicFileName):
    mixer.music.load(f"./musics/{MusicFileName}.mp3")

    global isPaused, totalSonglength, lastClicPos, timeLastClic
    isPaused = False

    music = MP3(f'./musics/{MusicFileName}.mp3')
    totalSonglength = music.info.length

    lengthMinutes = int(totalSonglength)//60

    if len(str(int(totalSonglength) % 60)) == 1:
        lengthSeconds = "0"+str(int(totalSonglength) % 60)
    else:
        lengthSeconds = int(totalSonglength) % 60
    canvas.itemconfig(totalTimeText, text=f"{lengthMinutes}:{lengthSeconds}")

    imageResumePause = ImageTk.PhotoImage(
        Image.open(GetFile("PauseButton.png")))
    canvas.pauseResumeImage = imageResumePause
    PauseButton.configure(image=imageResumePause)

    lastClicPos = 0
    timeLastClic = 0

    UpdateGUI()
    mixer.music.play()
    Queue()
    Thread(target=UpdateSlider, args=()).start()
    Thread(target=UpdateTime, args=()).start()


def PauseResumeMusic(event=0):
    global isPaused
    if isPaused:
        mixer.music.unpause()
        imageResumePause = ImageTk.PhotoImage(
            Image.open(GetFile("PauseButton.png")))
    else:
        mixer.music.pause()
        imageResumePause = ImageTk.PhotoImage(
            Image.open(GetFile("ResumeButton.png")))
    canvas.pauseResumeImage = imageResumePause
    PauseButton.configure(image=imageResumePause)
    isPaused = not isPaused


def NextSong(event=0):
    if len(musicsList) == 0:
        return
    global x
    if len(musicsList) > x+1:
        x += 1
    else:
        x = 0
    PlayMusic(musicsList[x])


def PreviousSong(event=0):
    if len(musicsList) == 0:
        return
    global x
    if x == 0:
        x = len(musicsList)-1
    else:
        x -= 1
    PlayMusic(musicsList[x])


def AddMusicToList(link):
    try:
        link = link.split("&list", 1)[0]
        audio = YoutubeDL({}).extract_info(link, download=False)
        videoTitle = "{0}".format((audio['title']))

        videoTitle = sub(r"\([^()]*\)", "", videoTitle)
        videoTitle = sub(r"\[[^()]*\]", "", videoTitle)

        request = get(
            f"https://api.deezer.com/search/track?q={videoTitle}").json()

        artist = request["data"][0]["artist"]["name"]
        title = request["data"][0]["title_short"]

        name = ValidFileName(artist + " § " + title)

        if not path.exists(f"./musics/{name}.mp3"):
            options = YoutubeDL(
                {
                    'format': 'bestaudio',
                    'outtmpl': f'./musics/{name}.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            )

            audio = options.extract_info(link)

        musicsList.append(name)

        if len(musicsList) == 1:
            PlayMusic(name)
        else:
            UpdateGUI()

    except:
        return messagebox.showerror("Error", "There is a problem with the link or the music is protected by YouTube.")


def AskForSong():
    global askSongAlreadyOpen
    if askSongAlreadyOpen == True:
        return

    PopUp = Toplevel()

    PopUp.geometry("400x84")
    PopUp.configure(bg="#E3E3E3")
    PopUp.title('Choose a song')

    canvasPopUp = Canvas(
        PopUp,
        bg="#E3E3E3",
        height=84,
        width=400,
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )

    canvasPopUp.place(x=0, y=0)
    image_entreeText = PhotoImage(
        file=GetFile("entreeText.png"))
    entreeText = canvasPopUp.create_image(
        200.0,
        56.0,
        image=image_entreeText
    )

    entry_image_1 = PhotoImage(
        file=GetFile("entry_1.png"))
    entry_bg_1 = canvasPopUp.create_image(
        200.5,
        56.5,
        image=entry_image_1
    )
    entry_1 = Entry(
        PopUp,
        bd=0,
        bg="#C4C4C4",
        highlightthickness=0
    )
    entry_1.place(
        x=17.0,
        y=43.0,
        width=367.0,
        height=25.0
    )

    canvasPopUp.create_text(
        7.0,
        5.0,
        anchor="nw",
        text="Music's link (YouTube)",
        fill="#000000",
        font=("Inter Regular", 18 * -1)
    )
    PopUp.resizable(False, False)

    askSongAlreadyOpen = True

    def closeDemanderoot():
        global askSongAlreadyOpen
        askSongAlreadyOpen = False
        PopUp.destroy()

    PopUp.protocol("WM_DELETE_root", closeDemanderoot)

    entry_1.bind('<Return>', lambda function: [Thread(
        target=AddMusicToList, args=(entry_1.get(), )).start(), closeDemanderoot()])

    PopUp.mainloop()


def RandomQueue():
    if len(musicsList) == 0:
        return
    global x
    CurrentMusic = musicsList[x]
    musicsList.pop(x)
    shuffle(musicsList)
    musicsList.insert(0, CurrentMusic)
    x = 0
    UpdateGUI()


def UpdateSlider():
    playingPos = mixer.music.get_pos()
    global lastClicPos

    nexSliderValue = lastClicPos + \
        ((367-lastClicPos)*(playingPos/1000))/totalSonglength
    canvas.move(cursor, nexSliderValue-canvas.coords(cursor)[0], 0)

    root.after(1, UpdateSlider)


def UpdateTime():
    global timeLastClic
    playingPos = int(timeLastClic + mixer.music.get_pos()/1000)

    lengthMinutes = int(playingPos)//60

    if len(str(int(playingPos) % 60)) == 1:
        lengthSeconds = "0"+str(int(playingPos) % 60)
    else:
        lengthSeconds = int(playingPos) % 60

    canvas.itemconfig(currentTimeText, text=f"{lengthMinutes}:{lengthSeconds}")

    root.after(1, UpdateTime)


def clicSlider(eventorigin):
    global isPaused
    if len(musicsList) == 0:
        return
    x = eventorigin.x
    y = eventorigin.y
    if 325 < y < 335:
        global lastClicPos, timeLastClic
        lastClicPos = x
        timeLastClic = int(x*totalSonglength/367)

        mixer.music.play(0, int(x*totalSonglength/367))

        if isPaused == True:
            mixer.music.pause()


def ShowQueue():
    global queueAlreadyOpen
    if queueAlreadyOpen == True:
        return

    PopUp2 = Toplevel()

    PopUp2.geometry("400x400")
    PopUp2.configure(bg="#E3E3E3")
    PopUp2.title("Queue")

    canvasPopUp2 = Canvas(
        PopUp2,
        bg="#E3E3E3",
        height=400,
        width=400,
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )

    canvasPopUp2.place(x=0, y=0)
    canvasPopUp2.create_text(
        27.0,
        23.0,
        anchor="nw",
        text="Next...",
        fill="#000000",
        font=("Inter Medium", 24 * -1)
    )

    QueueList = canvasPopUp2.create_text(
        27.0,
        86.0,
        anchor="nw",
        text="It's empty here, isn't it ?\n",
        fill="#000000",
        font=("Inter Medium", 18 * -1)
    )

    def UpdateQueue():
        global musicsList
        if len(musicsList) > x+1:
            canvasPopUp2.itemconfig(textInfo, text="")
            canvasPopUp2.itemconfig(QueueList, text='\n'.join(
                musicsList[x+1:len(musicsList)]).replace("§", "-"))
        else:
            canvasPopUp2.itemconfig(
                QueueList, text="It's empty here, isn't it ?\n")
            canvasPopUp2.itemconfig(
                textInfo, text="To add music to\nyour SpautiNoFay queue,\nclick on the +")
        PopUp2.after(1, UpdateQueue)

    textInfo = canvasPopUp2.create_text(
        27.0,
        149.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter Medium", 20 * -1)
    )
    UpdateQueue()

    queueAlreadyOpen = True

    def closeFileAttente():
        global queueAlreadyOpen
        queueAlreadyOpen = False
        PopUp2.destroy()

    PopUp2.protocol("WM_DELETE_root", closeFileAttente)

    PopUp2.resizable(False, True)
    PopUp2.mainloop()


root.geometry("367x479")
root.configure(bg="#E3E3E3")
root.title('SpautiNoFay')
root.resizable(False, False)

# ------------------------------------------------
# ONLY WINDOWS
root.iconbitmap("./assets/SpautiNoFay_icon.ico")
# ------------------------------------------------

canvas = Canvas(
    root,
    bg="#E3E3E3",
    height=479,
    width=367,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)
canvas.create_rectangle(
    1.0,
    328.0,
    369.0,
    479.0,
    fill="#E7DBD0",
    outline="")

currentTimeText = canvas.create_text(
    20,
    345,
    anchor="nw",
    text="0:00",
    fill="#000000",
    font=("DMMono Medium", 12 * -1)
)

totalTimeText = canvas.create_text(
    320,
    345,
    anchor="nw",
    text="0:00",
    fill="#000000",
    font=("DMMono Medium", 12 * -1)
)

imageRandomButton = PhotoImage(
    file=GetFile("RandomButton.png"))
RandomButton = Button(
    cursor="hand2",
    image=imageRandomButton,
    borderwidth=0,
    highlightthickness=0,
    command=RandomQueue,
    relief="flat"
)
RandomButton.place(
    x=24.0,
    y=388.71820068359375,
    width=36.86767578125,
    height=36.86773681640625
)

imagePreviousButton = PhotoImage(
    file=GetFile("PreviousButton.png"))
PreviousButton = Button(
    cursor="hand2",
    image=imagePreviousButton,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: Thread(target=PreviousSong, args=()).start(),
    relief="flat"
)
PreviousButton.place(
    x=83.3741455078125,
    y=384.6456298828125,
    width=45.012939453125,
    height=45.012939453125
)

imagePauseButton = PhotoImage(
    file=GetFile("PauseButton.png"))
PauseButton = Button(
    cursor="hand2",
    image=imagePauseButton,
    borderwidth=0,
    highlightthickness=0,
    command=PauseResumeMusic,
    relief="flat"
)
PauseButton.place(
    x=151.0,
    y=375.0,
    width=66.0,
    height=65.0
)

imageNextButton = PhotoImage(
    file=GetFile("NextButton.png"))
NextButton = Button(
    cursor="hand2",
    image=imageNextButton,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: Thread(target=NextSong, args=()).start(),
    relief="flat"
)
NextButton.place(
    x=237.7041015625,
    y=384.6456298828125,
    width=45.012939453125,
    height=45.012939453125
)

imagePlusButton = PhotoImage(
    file=GetFile("PlusButton.png"))
PlusButton = Button(
    cursor="hand2",
    image=imagePlusButton,
    borderwidth=0,
    highlightthickness=0,
    command=AskForSong,
    relief="flat"
)
PlusButton.place(
    x=305.2235107421875,
    y=388.71820068359375,
    width=36.86767578125,
    height=36.86773681640625
)

imageAlbumCoverGrey = PhotoImage(
    file=GetFile("AlbumCoverGrey.png"))
AlbumCover = canvas.create_image(
    82.0,
    247.0,
    image=imageAlbumCoverGrey
)

CurrentTitleText = canvas.create_text(
    161.0,
    183.0,
    anchor="nw",
    text="Title",
    fill="#000000",
    font=("Inter Medium", 18 * -1)
)

CurrentArtistText = canvas.create_text(
    161.0,
    205.0,
    anchor="nw",
    text="Artist",
    fill="#6A6A6A",
    font=("Inter Medium", 18 * -1)
)

imageArtistPicture = PhotoImage(
    file=GetFile("ArtistPicture.png"))
ArtistPicture = canvas.create_image(
    191.0,
    264.0,
    image=imageArtistPicture
)

canvas.create_text(
    19.0,
    143.0,
    anchor="nw",
    text="Current song",
    fill="#000000",
    font=("Inter Medium", 24 * -1)
)

canvas.create_text(
    17.0,
    14.0,
    anchor="nw",
    text="Next...",
    fill="#000000",
    font=("Inter Medium", 24 * -1)
)

imageRectangleNextTitle = PhotoImage(
    file=GetFile("RectangleNextTitle.png"))
RectangleNextTitle = canvas.create_image(
    183.0,
    89.0,
    image=imageRectangleNextTitle
)

NextTitleText = canvas.create_text(
    96.1273193359375,
    63.5,
    anchor="nw",
    text="Next title",
    fill="#E3E3E3",
    font=("Inter Medium", 17 * -1)
)

NextArtistText = canvas.create_text(
    96.1273193359375,
    93.6890869140625,
    anchor="nw",
    text="Next artist",
    fill="#FFFFFF",
    font=("Inter Medium", 14 * -1)
)

imageNextArtistGrey = PhotoImage(
    file=GetFile("NextArtistGrey.png"))
NextArtist = canvas.create_image(
    59.1273193359375,
    89.5,
    image=imageNextArtistGrey
)

imagePlayButton = PhotoImage(
    file=GetFile("PlayButton.png"))
PlayButton = Button(
    cursor="hand2",
    image=imagePlayButton,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: Thread(target=NextSong, args=()).start(),
    relief="flat"
)
PlayButton.place(
    x=238.0,
    y=72.0,
    width=102.0,
    height=39.0
)

imageSliderBar = PhotoImage(
    file=GetFile("image_5.png"))
SliderBar = canvas.create_image(
    183.0,
    329.0,
    image=imageSliderBar
)

imagecursor = PhotoImage(
    file=GetFile("image_6.png"))
cursor = canvas.create_image(
    0.0,
    328.50,
    image=imagecursor
)

image_image_7 = PhotoImage(
    file=GetFile("image_7.png"))
image_7 = canvas.create_image(
    59.0,
    90.0,
    image=image_image_7
)

image_image_8 = PhotoImage(
    file=GetFile("image_8.png"))
image_8 = canvas.create_image(
    191.0,
    264.0,
    image=image_image_8
)

imageAlbumCover = PhotoImage(
    file=GetFile("image_9.png"))
masqueAlbumCover = canvas.create_image(
    82.0,
    247.0,
    image=imageAlbumCover
)

imageQueueButton = PhotoImage(
    file=GetFile("QueueButton.png"))
QueueButton = Button(
    cursor="hand2",
    image=imageQueueButton,
    borderwidth=0,
    highlightthickness=0,
    command=ShowQueue,
    relief="flat"
)
QueueButton.place(
    x=313.0,
    y=16.0,
    width=34.0,
    height=30.0
)

splash_image = ImageTk.PhotoImage(Image.open(GetFile("splash-screen.png")))
splash_screen = Label(root, image=splash_image)
splash_screen.pack(side="bottom", fill="both", expand="yes")

root.after(2000, splash_screen.destroy)

root.bind("<Button 1>", clicSlider)
root.bind("<space>", PauseResumeMusic)
root.bind("<Left>", PreviousSong)
root.bind("<Right>", NextSong)

root.mainloop()
