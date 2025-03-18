
jQuery(document).ready(function($) {
    'use strict';

    // ============================================================== 
    // Notification list
    // ============================================================== 
    if ($(".notification-list").length) {

        $('.notification-list').slimScroll({
            height: '250px'
        });

    }

    // ============================================================== 
    // Menu Slim Scroll List
    // ============================================================== 


    if ($(".menu-list").length) {
        $('.menu-list').slimScroll({

        });
    }

    // ============================================================== 
    // Sidebar scrollnavigation 
    // ============================================================== 

    if ($(".sidebar-nav-fixed a").length) {
        $('.sidebar-nav-fixed a')
            // Remove links that don't actually link to anything

            .click(function(event) {
                // On-page links
                if (
                    location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') &&
                    location.hostname == this.hostname
                ) {
                    // Figure out element to scroll to
                    var target = $(this.hash);
                    target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
                    // Does a scroll target exist?
                    if (target.length) {
                        // Only prevent default if animation is actually gonna happen
                        event.preventDefault();
                        $('html, body').animate({
                            scrollTop: target.offset().top - 90
                        }, 1000, function() {
                            // Callback after animation
                            // Must change focus!
                            var $target = $(target);
                            $target.focus();
                            if ($target.is(":focus")) { // Checking if the target was focused
                                return false;
                            } else {
                                $target.attr('tabindex', '-1'); // Adding tabindex for elements not focusable
                                $target.focus(); // Set focus again
                            };
                        });
                    }
                };
                $('.sidebar-nav-fixed a').each(function() {
                    $(this).removeClass('active');
                })
                $(this).addClass('active');
            });

    }

    // ============================================================== 
    // tooltip
    // ============================================================== 
    if ($('[data-toggle="tooltip"]').length) {
            
            $('[data-toggle="tooltip"]').tooltip()

        }

     // ============================================================== 
    // popover
    // ============================================================== 
       if ($('[data-toggle="popover"]').length) {
            $('[data-toggle="popover"]').popover()

    }
     // ============================================================== 
    // Chat List Slim Scroll
    // ============================================================== 
        

        if ($('.chat-list').length) {
            $('.chat-list').slimScroll({
            color: 'false',
            width: '100%'


        });
    }
    // ============================================================== 
    // dropzone script
    // ============================================================== 

 //     if ($('.dz-clickable').length) {
 //            $(".dz-clickable").dropzone({ url: "/file/post" });
 // }

    $(".addToCart").click(function (e) {
    e.preventDefault();
    let wanted_index = $(this).closest("tr").index()
    let products = document.getElementsByClassName("prod_id")

    let product_wanted = products[wanted_index]
    console.log(product_wanted)
    let product_id = product_wanted.value;
    console.log(product_id)
    let token = $("input[name=csrfmiddlewaretoken]").val();
    console.log(token)
    $.ajax({
      method: "POST",
      url: "/add_to_cart/",
      data: {
        product_id: product_id,
        csrfmiddlewaretoken: token,
      },
      success: function (response) {
          alertify.set('notifier','position', 'top-right');
          alertify.success(response.status);
        // Swal.fire({text: response.status, position: 'top-end', timer: 1000, showConfirmButton:false, icon:response.icon});
      },
    });
  });

   $("body").on('click', '.addToCartFromHome', function (e) {
    e.preventDefault();
    let wanted_index = $(this).closest("tr").index()
    let products = document.getElementsByClassName("prod_id")

    let product_wanted = products[wanted_index]
    console.log(product_wanted)
    let product_id = product_wanted.value;
    console.log(product_id)

    console.log(product_id)
    let token = $("input[name=csrfmiddlewaretoken]").val();
    console.log(token)
    $.ajax({
      method: "POST",
      url: "/add_to_cart/",
      data: {
        product_id: product_id,
        csrfmiddlewaretoken: token,
      },
      success: function (response) {
          alertify.set('notifier','position', 'top-right');
          alertify.success(response.status);
        // Swal.fire({text: response.status, position: 'top-end', timer: 1000, showConfirmButton:false, icon:response.icon});
        $(".cart-box").load(location.href + " .cart-box");
      },
    });
  });

   // $("body").on('click', '.sell_items', function (e){
   //     e.preventDefault()
   //
   //     let token = $("input[name=csrfmiddlewaretoken]").val();
   //
   //     $.ajax({
   //        method: "POST",
   //        url: "/sell_items/",
   //        data: {
   //          csrfmiddlewaretoken: token,
   //        },
   //        success: function (response) {
   //          Swal.fire({text: response.status, position: 'top-end', timer: 1000, showConfirmButton:false, icon:response.icon});
   //          $(".cart-box").load(location.href + " .cart-box");
   //          $(".table").load(location.href + " .table");
   //          window.location.assign("{% url 'all_sales' %}")
   //        },
   //      });
   // })



   $("body").on('click', '.deleteCartItem', function(e) {
    e.preventDefault();

    let wanted_index = $(this).closest("li").index()
    console.log(wanted_index)
    let cart_items = document.getElementsByClassName("cart_item_id")

    let cart_item = cart_items[wanted_index]
    console.log(cart_item)
    let product_id = cart_item.value;

    console.log(product_id)
    let token = $("input[name=csrfmiddlewaretoken]").val();
    console.log(token)
    $.ajax({
      method: "POST",
      url: "/delete_cart_item/",
      data: {
        product_id: product_id,
        csrfmiddlewaretoken: token,
      },
      success: function (response) {
          alertify.set('notifier','position', 'top-right');
          alertify.success(response.status);
        // Swal.fire({text: response.status, position: 'top-end', timer: 1000, showConfirmButton:false});
        $(".cart-box").load(location.href + " .cart-box");
      },
    });
  });




}); // END OF JQUERY


// $(function() {
//     "use strict";


    

   // var monkeyList = new List('test-list', {
    //    valueNames: ['name']

     // });
  // var monkeyList = new List('test-list-2', {
    //    valueNames: ['name']

   // });



   
   

// });