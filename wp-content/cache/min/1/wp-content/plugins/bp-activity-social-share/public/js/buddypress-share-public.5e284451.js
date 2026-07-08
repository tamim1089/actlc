(function($){'use strict';$(document).ready(function(){$(document).on('click',".bp-share-button",function(e){$(this).parent().next(".service-buttons").toggle(500)});$(document).on("click",".bp-share.has-popup",function(e){var display_attr=$(this).attr('attr-display');if('no-popup'!=display_attr){e.preventDefault();console.log(display_attr);goclicky($(this).attr("href"))}});function FindLeftWindowBoundry(){if(window.screenLeft){return window.screenLeft}
if(window.screenX)
return window.screenX;return 0}
function FindTopWindowBoundry(){if(window.screenTop){return window.screenTop}
if(window.screenY)
return window.screenY;return 0}
function goclicky(meh){console.log(FindLeftWindowBoundry(),FindTopWindowBoundry());var x=screen.width/2-700/2+FindLeftWindowBoundry();var y=screen.height/2-450/2+FindTopWindowBoundry();window.open(meh,'','height=485,width=700,left='+x+',top='+y)}
$(document).on('click',".bp-cpoy",function(e){e.preventDefault();var copyText=$(this).data('href');document.addEventListener('copy',function(e){e.clipboardData.setData('text/plain',copyText);e.preventDefault()},!0);document.execCommand('copy');var tooltip=$(this).next();tooltip.removeClass('tooltip-hide');setTimeout(function(){tooltip.addClass('tooltip-hide')},500)})})})(jQuery)