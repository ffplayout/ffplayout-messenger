# messenger
ffmpeg can include the **libzmq** library, this makes it possible to mapiulate filters in real time.

This library we use to communicate with the drawtext filter in ffplayout. This give us the option to send text to the stream in any format which are supported from the drawtext filter.

![messenger](./assets/screenshot.png)

The messenger needs the [ffplayout-api](https://github.com/ffplayout/ffplayout-api) to send the commands to the engine.
**It is highly recommended to run this application only behind a proxy with ssl - for example nginx.**

### Expression:
**drawtext** can be controlled with different expressions for fading, or moving, the client will have some examples, for more take a look in the [filter settings](https://ffmpeg.org/ffmpeg-filters.html#drawtext-1) and in the [expression parameters](https://ffmpeg.org/ffmpeg-all.html#Expression-Evaluation).

Please don't ask in the issues about help for different kind of expressions. This is only a GUI for the ffmpeg settings. A better place for this kind of help is [stackoverflow](https://stackoverflow.com/).

If you have some nice and useful expressions you are welcome to share them with us. I'm happy to integrate them in the GUI as a preset or example.

### Testing/Preview
When you add new expressions to the client, you should always test them, before you send them to ffplayout. A wrong command can crash the playout.

### Configuration
To configure edit: [messenger.ini](./assets/messenger.ini)

### Requirements
- ffmpeg must be compiled with **libzmq**
- python 3.6+
- **pyside2** python module on the client side
- ffplay with libzmq for the client
