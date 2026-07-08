function mec_fluent_wrap_init() {

    monthlyCalendarUI();
}

function monthlyCalendarUI() {
    jQuery(".mec-fluent-monthly-wrap").length < 1 || (jQuery(window).innerWidth() <= 767 ? jQuery("dt.mec-calendar-day").each(function (e, n) {
        var t, c, r, o = jQuery(n);
        0 < o.find(".mec-more-events-mobile").length || (c = o.children(".simple-skin-ended")).length < 1 || (t = [], c.each(function (e, n) {
            var c = (o = jQuery(n)).clone().empty().addClass("mec-more-event-copy"),
                r = o.find(".mec-event-title")[0].outerHTML,
                o = (n = '<span class="mec-event-start-time">' + o.data("start-time") + "</span>", '<span class="mec-event-end-time">' + o.data("end-time") + "</span>");
            c.append('\n<div class="mec-more-events-content">\n'.concat(r, '\n<i class="mec-sl-clock"></i>\n').concat(n, "\n").concat(o, "\n</div>")), t[e] = c[0].outerHTML
        }), o.find(".mec-more-events-wrap").length < 1 && (r = o.data("day"), n = o.data("month"), c = o.data("year"), r = new Date(c, n - 1, r, 0, 0, 0, 0), r = dateFormat(r, "fullDate"), r = '\n<span class="mec-more-events-icon">...</span>\n<div class="mec-more-events-wrap mec-more-events-generated" style="display: none;">\n<div class="mec-more-events">\n<h5 class="mec-more-events-header">'.concat(r, '</h5>\n<div class="mec-more-events-body"></div>\n</div>\n</div>'), o.append(r)), t.forEach(function (e) {
            o.find(".mec-more-events-wrap").addClass("mec-more-events-mobile").end().find(".mec-more-events-body").prepend(e)
        }))
    }) : (jQuery(".mec-more-events-generated").siblings(".mec-more-events-icon").remove().end().remove(), jQuery(".mec-more-events-wrap.mec-more-events-mobile").removeClass("mec-more-events-mobile").find(".mec-more-event-copy").remove()))
}

function customScrollbar() {
    var e;
    jQuery(".mec-fluent-wrap").length < 0 || jQuery().niceScroll && ((e = jQuery(this)).siblings(".mec-more-events-wrap").find(".mec-more-events-body").hasClass("mec-custom-scrollbar") || e.siblings(".mec-more-events-wrap").find(".mec-more-events-body").addClass("mec-custom-scrollbar").niceScroll({
        cursorcolor: "#C7EBFB",
        cursorwidth: "4px",
        cursorborderradius: "4px",
        cursorborder: "none",
        railoffset: {
            left: -2
        }
    }), e.siblings(".mec-more-events-wrap").find(".mec-more-events-body").getNiceScroll().onResize())
}
var mec_load_skin_handler = function (e, n) {
    n = jQuery(n), jQuery(".mec-searchbar-category-wrap select", n).select2(), jQuery("select", n).niceSelect()
    //jQuery(document).mecSearchForm({}) //TODO: check
};

jQuery(document).ready(function($){

    if( jQuery(".mec-fluent-wrap").length ){

    }

    jQuery(document).on("click", ".mec-fluent-wrap .mec-more-events-icon", customScrollbar);
    jQuery(document).on("load_calendar_data", function () {
        monthlyCalendarUI()
    });

    jQuery(window).on("resize", monthlyCalendarUI);
    jQuery(document).on("mec_load_skin_success", mec_load_skin_handler);
    jQuery(document).on("mec_search_success", mec_load_skin_handler);
    jQuery(document).on("mec_before_load_skin_success", function(e,wrap, id){

        if( false !== $("#mec_skin_" + id).hasClass('mec-fluent-wrap') ){

            delete mec_search_callbacks[id];
        }
    });

    mec_fluent_wrap_init();
});