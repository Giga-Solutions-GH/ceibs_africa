// init_tempus.js
(function($) {
  $(function() {
    // Initialize all date inputs with a parent div having data-target attribute
    $('.datetimepicker-input').each(function(){
      // Find the closest parent with .input-group.date
      var $container = $(this).closest('.input-group.date');
      if ($container.length) {
        $container.datetimepicker();
      }
    });
  });
})(django.jQuery);
