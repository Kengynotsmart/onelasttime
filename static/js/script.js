(function($) {

  "use strict";

  // init Chocolat light box
  var initChocolat = function() {
  Chocolat(document.querySelectorAll('.image-link'), {
      imageSize: 'contain',
      loop: true,
    })
  }

  // document ready
  $(document).ready(function(){
    initChocolat();
  });

})(jQuery);