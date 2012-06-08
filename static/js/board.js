// Make the cards be sortable.

var CardGrid = (function ($) {
    // Poll for updates from the server.
    var pendingPoll;
    var pendingPollUrl;

    function pollForUpdates(url) {
        if (!$('body').hasClass('polling')) {
            $('body').addClass('polling');
            $.ajax(url, {type: 'GET', dataType: 'json'})
                .done(onPollSuccess)
                .always(onPollComplete);
        }
    }

    function onPollSuccess(data, textStatus, jqXHR) {
        if (data.ready && data.events) {
            for (var i = 0; i < data.events.length; ++i) {
                var event = data.events[i];
                if (event.type === 'rearrange' && event.dropped && event.order) {
                    var droppedSelector = '#card-' + event.dropped;
                    var succID = event.order[1];
                    if (succID === null) {
                        // This card was dropped at the end of its bin.
                        var binSelector = (event.tags && event.tags.length > 0
                                ? '#bin-' + event.tags.join('-')
                                : '#untagged-bin');
                         $(droppedSelector).appendTo(binSelector);
                        console.log(droppedSelector + '.appendTo ' + binSelector);
                    } else {
                        // This card was dropped before another.
                        var succSelector = '#card-' + succID;
                        $(droppedSelector).insertBefore(succSelector);
                        console.log(droppedSelector + '.insertBefore ' + succSelector);
                    }
                }
            }
        }

        if (data.next) {
            pendingPollUrl = data.next;
            pendingPoll = window.setTimeout(pollAgain, data.pleaseWait || 100);
        }
    }

    function onPollComplete(jqXHT, textStatus) {
        $('body').removeClass('polling');
    }

    function pollAgain() {
        pendingPoll = null;
        pollForUpdates(pendingPollUrl);
    }

    function addMessage(msg) {
        alert(msg);
    }

    function enableRearrange(ajaxUrl) {
      // Make the card bins be sortable with drag-and-drop.
      $('.card-bin').sortable({
        connectWith: '.card-bin',
        update: function (event, ui) {
            // Report the change to the server.
            var droppedID = ui.item.attr('id').replace(/^card-/, '');
            var eltIDs = $(this).sortable('toArray');
            var cardIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                cardIDs.push(eltIDs[i].replace(/^card-/, ''));
            }

            // Turns out MSIE does not support Array.indexOf.
            var droppedIndex  = cardIDs.length;
            while(--droppedIndex >= 0) {
                if  (cardIDs[droppedIndex] == droppedID) {
                    break;
                }
            }
            if (droppedIndex >= 0) {
                var succID = (droppedIndex + 1 < cardIDs.length ? cardIDs[droppedIndex + 1] : '-');
                var abbreviatedIDs = [droppedID, succID];

                var form$ = $(this).parent().find('form');
                if (ajaxUrl) {
                    var data = {}
                    var es = $('input[type=hidden]', form$).get();
                    for (var i = 0; i < es.length; ++i) {
                        data[es[i].name] = es[i].value;
                    }
                    data[ 'order'] =  abbreviatedIDs.join(' ');
                    data['dropped'] = droppedID;
                    ui.item.addClass('ajax-loading');
                    $.ajax(ajaxUrl, {
                        type: 'POST',
                        dataType: 'json',
                        data: data
                    }).error(function (jqXHT) {
                        CardGrid.addMessage('Failed to store the new position of the card '
                        + 'on the server: refresh this page to see their real positions.')
                    }).always(function () {
                        ui.item.removeClass('ajax-loading');
                    });
                } else {
                    $('input[name=order]', form$).val(abbreviatedIDs.join(' '));
                    $('input[name=dropped]', form$).val(droppedID);
                }
            }
        }
      })
       .disableSelection()
       .parent().find('form').hide();
    }

    function addCloseButtonToMessages() {
        $('.messages').each(function (index, elt) {
            $('<a>', {
                href: 'javascript:void(0)',
                text: 'close',
                click: function () {
                    $(elt).remove();
                }
            }).appendTo(elt);
        });
    }

    return {
        addCloseButtonToMessages: addCloseButtonToMessages,
        enableRearrange: enableRearrange,
        pollForUpdates: pollForUpdates,
        addMessage: addMessage
    };
})(jQuery);

