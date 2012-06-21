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

    function enableRearrange(binSelector, ajaxUrl) {
      // Make the card bins be sortable with drag-and-drop.
      $(binSelector).sortable({
        connectWith: binSelector,
        update: function (event, ui) {
            // Report the change to the server.
            var droppedID = ui.item.attr('id').replace(/^[a-z]+-/, '');
            var eltIDs = $(this).sortable('toArray');
            var cardIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                cardIDs.push(eltIDs[i].replace(/^[a-z]+-/, ''));
            }

            // Turns out MSIE does not support Array.indexOf.
            var droppedIndex  = cardIDs.length;
            while (--droppedIndex >= 0) {
                if  (cardIDs[droppedIndex] == droppedID) {
                    break;
                }
            }
            if (droppedIndex >= 0) {
                var succID = (droppedIndex + 1 < cardIDs.length ? cardIDs[droppedIndex + 1] : '-');
                var abbreviatedIDs = [droppedID, succID];

                var form$ = $(this).parent().find('form');
                if (ajaxUrl) {
                    var data = {
                        order: abbreviatedIDs.join(' '),
                        dropped: droppedID
                    };

                    // Copy tag IDs (applicable to arranging cards on the grid).
                    var es = $('input[type=hidden]', form$).get();
                    for (var i = 0; i < es.length; ++i) {
                        data[es[i].name] = es[i].value;
                    }

                    // Send to the server.
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

    function makeNewCardButtonMagic() {
        var form = $('#new-card-form').remove();
        $('#new-card-link').click(function (event) {
            var cell =  $('#card-grid td').get(0);
            form.appendTo(cell);
            form.slideDown();
            $('#new-card-link').addClass('disabled');
            $('.buttons a', form).click(function (ev) {
                form.remove();
                $('#new-card-link').removeClass('disabled');
            });
            $('#id_label').focus();
        });
        addCancelLinkToForm(form);
    }

    function addCancelLinkToForm(form) {
        var buttons = form.find('.buttons');
        $('<span>', {text: 'or '}).appendTo(buttons);
        $('<a/>', {
            href: '#menu',
            text: 'Cancel',
        }).appendTo(buttons);
        return form;
    }

    function addAddButtonToList(listSelector, formSelector) {
        var form = $(formSelector).remove();
        addCancelLinkToForm(form);

        var section = $(listSelector).closest('section');
        var buttonBar = $('ul.menu', section);
        if (buttonBar.size() == 0) {
            buttonBar = $('<div>', {'class': 'menu'})
                .appendTo(section);
        }
        var buttonLink = $('<a>', {
            href: '#' + form.attr('id'),
            text: $('input[type=submit]', form).val() + '…',
            click: function (ev) {
                if (!buttonLink.hasClass('disabled')) {
                    $(listSelector).append(form);
                    form.slideDown();
                    buttonLink.addClass('disabled')
                    $('.buttons a', form).click(function (ev) {
                        form.remove();
                        buttonLink.removeClass('disabled');
                    });
                }
            }
        });
        $('<li>').append(buttonLink).prependTo(buttonBar);
    }

    return {
        addCloseButtonToMessages: addCloseButtonToMessages,
        addAddButtonToList: addAddButtonToList,
        makeNewCardButtonMagic: makeNewCardButtonMagic,
        enableRearrange: enableRearrange,
        pollForUpdates: pollForUpdates,
        addMessage: addMessage
    };
})(jQuery);

$('body').removeClass('no-js').addClass('js');

