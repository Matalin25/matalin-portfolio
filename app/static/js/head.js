/* Устанавливает признак работающего JS — до отрисовки страницы.
   Нужен, чтобы анимации появления не «прятали» контент без скриптов. */
document.documentElement.classList.remove('no-js');
document.documentElement.classList.add('js');
