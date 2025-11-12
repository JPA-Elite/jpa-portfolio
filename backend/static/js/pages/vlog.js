document.addEventListener("DOMContentLoaded", function () {
    const players = Array.from(document.querySelectorAll('.player')).map((player) => new Plyr(player));

    players.forEach((player, index, playerList) => {
        player.on('play', () => {
            playerList.forEach((otherPlayer, otherIndex) => {
                if (otherIndex !== index && !otherPlayer.paused) {
                    otherPlayer.pause();
                }
            });
        });
    });
});