from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

def listing(request, id):
    listing_details = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listing_details.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_details)
    is_owner = request.user.username == listing_details.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listing_details,
        "isListingInWatchlist": isListingInWatchlist,
        "all_comments": all_comments,
        "is_owner": is_owner
    })

def closeAuction(request, id):
    listing_details = Listing.objects.get(pk=id)
    listing_details.isActive = False
    listing_details.save()
    isListingInWatchlist = request.user in listing_details.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_details)
    is_owner = request.user.username == listing_details.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listing_details,
        "isListingInWatchlist": isListingInWatchlist,
        "all_comments": all_comments,
        "is_owner": is_owner,
        "update": True,
        "message": "Congratulations! Your auction is closed"
    })


def addBid(request, id):
    new_bid = request.POST['newBid']
    listing_details = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listing_details.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_details)
    is_owner = request.user.username == listing_details.owner.username
    if int(new_bid) > listing_details.price.bid:
        update_bid = Bid(user=request.user, bid=int(new_bid))
        update_bid.save()
        listing_details.price = update_bid
        listing_details.save()
        return render(request, "auctions/listing.html", {
            "listing": listing_details,
            "message": "Bid Was Updated Successfully",
            "update": True,
            "isListingInWatchlist": isListingInWatchlist,
            'all_comments': all_comments,
            "is_owner": is_owner
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listing_details,
            "message": "Bid Could Not Be Able To Update Successfully",
            "update": False,
            "isListingInWatchlist": isListingInWatchlist,
            'all_comments': all_comments,
            "is_owner": is_owner
        })

def addComment(request, id):
    currentUser = request.user
    listing_details = Listing.objects.get(pk=id)
    message = request.POST["newComment"]
    newComment = Comment (
        author=currentUser,
        listing=listing_details,
        message=message
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist(request):
    current_user = request.user
    listings = current_user.listingWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })


def removeWatchList(request, id):
    listing_details = Listing.objects.get(pk=id)
    current_user = request.user
    listing_details.watchlist.remove(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def addWatchList(request, id):
    listing_details = Listing.objects.get(pk=id)
    current_user = request.user
    listing_details.watchlist.add(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def index(request):
    active_listings = Listing.objects.filter(isActive=True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listings,
        "categories": all_categories
    })

def display_category(request):
    if request.method == "POST":
        category_from_form = request.POST["category"]
        category = Category.objects.get(categoryName=category_from_form)
        active_listings = Listing.objects.filter(isActive=True, category=category)
        all_categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": active_listings,
            "categories": all_categories
        })

def create_listing(request):
    if request.method == "GET":
        all_categories=Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": all_categories,
        })
    else: 
        title = request.POST["title"]
        description = request.POST["description"]
        image_url = request.POST["image_url"]
        price = request.POST["price"]
        category = request.POST["category"]
        current_user = request.user
        category_instance = Category.objects.get(categoryName=category)
        bid = Bid(bid=int(price), user=current_user)
        bid.save()
        new_listing = Listing(
            title=title,
            description=description,
            imageUrl=image_url,
            price=bid,
            category=category_instance,
            owner=current_user
        )

        new_listing.save()
        return HttpResponseRedirect(reverse(index))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
